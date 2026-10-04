import bpy
import bmesh
import numpy as np
from .geometry import MeshGeometry
from .flow import compute_flow_and_gravity
from .occlusion import compute_occlusion

def slice_mesh(obj, settings):
    """
    Основная функция нарезки:
    1. Собирает геометрию.
    2. Вычисляет все оценки ребер.
    3. Принимает решение и размечает швы (seams).
    4. Запускает развертку в Blender.
    """
    # 1. Собираем геометрию
    try:
        geometry = MeshGeometry(obj)
    except Exception as e:
        print(f"Ошибка при анализе геометрии: {e}")
        return False
    
    num_edges = geometry.num_edges
    if num_edges == 0:
        geometry.free()
        return False

    # 2. Вычисляем угол между полигонами для каждого ребра (в градусах)
    edge_angles = np.zeros(num_edges)
    for i in range(num_edges):
        connected_faces = geometry.edge_to_faces[i]
        if len(connected_faces) == 2:
            n_a = geometry.face_normals_world[connected_faces[0]]
            n_b = geometry.face_normals_world[connected_faces[1]]
            
            # Косинус угла между нормалями соседних полигонов
            cos_angle = np.clip(np.dot(n_a, n_b), -1.0, 1.0)
            # Угол в градусах
            edge_angles[i] = np.degrees(np.arccos(cos_angle))

    # 3. Вычисляем оценки гравитации и затененности
    watershed_bonus, vertical_penalty = compute_flow_and_gravity(geometry, settings)
    occlusion_bonus = compute_occlusion(geometry, settings)

    # 4. Расчет итогового балла для каждого ребра
    scores = np.zeros(num_edges)
    
    for i in range(num_edges):
        connected_faces = geometry.edge_to_faces[i]
        
        # Граничные ребра (у которых только один полигон) уже являются швами по умолчанию,
        # нам не нужно отмечать их как швы в Blender.
        if len(connected_faces) < 2:
            continue
            
        angle = edge_angles[i]
        
        # --- ПОЛЗУНОК ДЕФОРМАЦИИ (Базовая оценка по углу) ---
        # Если угол стыка больше 90 градусов, это очень острый стык (балл = 1.0)
        angle_score = min(angle / 90.0, 1.0)
        
        # Применяем порог деформации (threshold_angle)
        threshold = settings.threshold_angle
        if angle < threshold:
            # Если угол меньше порога, сильно уменьшаем вероятность разреза
            # (это заставит текстуру слегка потянуться, но остаться целой)
            if threshold > 0:
                angle_score *= (angle / threshold) ** 2
            else:
                angle_score = 0.0

        # Формула: Базовый угол + Водораздел + Затенение - Защита вертикалей
        scores[i] = (
            angle_score 
            + watershed_bonus[i] 
            + occlusion_bonus[i] 
            - vertical_penalty[i]
        )

    # 5. Перенос швов в BMesh
    # Очищаем старые швы и размечаем новые, если балл ребра выше порога (0.5)
    seams_count = 0
    for i, edge in enumerate(geometry.bm.edges):
        # Только для внутренних ребер (не границ)
        if len(geometry.edge_to_faces[i]) == 2:
            if scores[i] > 0.5:
                edge.seam = True
                seams_count += 1
            else:
                edge.seam = False

    # Записываем изменения обратно в меш объекта
    geometry.bm.to_mesh(obj.data)
    geometry.free()
    
    # 6. Запускаем стандартную развертку Blender
    # Для этого переключаемся в режим редактирования, выделяем все полигоны и вызываем Unwrap
    original_mode = obj.mode
    
    # Переходим в режим редактирования
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Выделяем всю геометрию
    bpy.ops.mesh.select_all(action='SELECT')
    
    # Запускаем развертку Blender
    # Используем стандартный алгоритм Angle Based (или Conformal, Blender выберет сам)
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)
    
    # Возвращаем исходный режим
    bpy.ops.object.mode_set(mode=original_mode)
    
    print(f"Размечено швов: {seams_count}")
    return True
