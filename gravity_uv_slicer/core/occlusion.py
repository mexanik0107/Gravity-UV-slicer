import bpy
from mathutils.bvhtree import BVHTree
from mathutils import Vector
import numpy as np

def compute_occlusion(geometry, settings):
    """
    Симулирует "лазерный радар" (рейкасты).
    Для каждого ребра пускает несколько лучей по полусфере его нормали.
    Возвращает оценку затененности ребра от 0.0 (открыто) до 1.0 (полностью скрыто).
    """
    occlusion_weight = settings.occlusion_weight
    if occlusion_weight < 1e-4:
        return np.zeros(geometry.num_edges)

    # 1. Создаем BVH-дерево для быстрого поиска пересечений лучей с моделью
    # Используем BMesh, который мы уже собрали в geometry
    bvh = BVHTree.FromBMesh(geometry.bm)
    if not bvh:
        return np.zeros(geometry.num_edges)

    # 2. Рассчитываем размер модели для масштабирования длины лучей
    # Находим диагональ габаритного контейнера модели
    local_coords = np.array([v.co for v in geometry.bm.verts])
    if len(local_coords) == 0:
        return np.zeros(geometry.num_edges)
        
    co_min = np.min(local_coords, axis=0)
    co_max = np.max(local_coords, axis=0)
    diagonal = np.linalg.norm(co_max - co_min)
    
    # Учитываем масштаб объекта в мире
    scale = geometry.obj.matrix_world.to_scale()
    avg_scale = (scale.x + scale.y + scale.z) / 3.0
    diagonal_world = diagonal * avg_scale
    
    # Максимальная дистанция луча - 15% от размера модели
    max_ray_distance = max(diagonal_world * 0.15, 0.05) # не меньше 5 см

    # 3. Подготовка локальных направлений лучей по полусфере (5 лучей)
    # 0: Прямо вверх по нормали
    # 1, 2: Наклоны влево-вправо на 45 градусов
    # 3, 4: Наклоны вперед-назад по направлению ребра на 45 градусов
    local_rays = [
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.707, 0.707]),
        np.array([0.0, 0.707, -0.707]),
        np.array([0.707, 0.707, 0.0]),
        np.array([-0.707, 0.707, 0.0])
    ]

    occlusion_scores = np.zeros(geometry.num_edges)

    # Небольшое смещение начала луча (1 мм), чтобы избежать самопересечения в точке старта
    offset_dist = 0.001 

    # 4. Обход всех ребер и пуск лучей
    for i in range(geometry.num_edges):
        connected_faces = geometry.edge_to_faces[i]
        if not connected_faces:
            continue
            
        # Определяем нормаль ребра как среднее нормалей прилегающих полигонов
        if len(connected_faces) == 2:
            n_edge = (geometry.face_normals_world[connected_faces[0]] + 
                      geometry.face_normals_world[connected_faces[1]]) * 0.5
        else:
            n_edge = geometry.face_normals_world[connected_faces[0]]
            
        n_edge_norm = np.linalg.norm(n_edge)
        if n_edge_norm > 1e-5:
            n_edge /= n_edge_norm
        else:
            # Если нормали противоположны (180 градусов), используем нормаль первого полигона
            n_edge = geometry.face_normals_world[connected_faces[0]]
            
        # Направление самого ребра
        e_dir = geometry.edge_dirs_world[i]
        
        # Третья ось для построения локального пространства ребра
        t_dir = np.cross(e_dir, n_edge)
        t_dir_norm = np.linalg.norm(t_dir)
        if t_dir_norm > 1e-5:
            t_dir /= t_dir_norm
        else:
            # В случае коллинеарности строим ортогональный вектор вручную
            t_dir = np.array([n_edge[1], -n_edge[0], 0.0])
            t_dir_norm = np.linalg.norm(t_dir)
            if t_dir_norm > 1e-5:
                t_dir /= t_dir_norm
            else:
                t_dir = np.array([1.0, 0.0, 0.0])

        # Точка старта луча с микро-смещением по нормали ребра
        origin_np = geometry.edge_centers_world[i] + n_edge * offset_dist
        origin_vec = Vector((origin_np[0], origin_np[1], origin_np[2]))
        
        hits = 0
        for ray_loc in local_rays:
            # Переводим направление луча из локального пространства ребра в мировое
            # ray_loc[0] * e_dir (вдоль ребра) + ray_loc[1] * n_edge (по нормали) + ray_loc[2] * t_dir (вбок)
            ray_dir_np = ray_loc[0] * e_dir + ray_loc[1] * n_edge + ray_loc[2] * t_dir
            ray_dir_norm = np.linalg.norm(ray_dir_np)
            if ray_dir_norm > 1e-5:
                ray_dir_np /= ray_dir_norm
                
            ray_dir_vec = Vector((ray_dir_np[0], ray_dir_np[1], ray_dir_np[2]))
            
            # Делаем быстрый рейкаст через BVH
            hit_loc, hit_normal, hit_index, hit_dist = bvh.ray_cast(origin_vec, ray_dir_vec, max_ray_distance)
            
            if hit_loc is not None:
                hits += 1
                
        # Оценка затененности - доля заблокированных лучей (от 0 до 1)
        occlusion_scores[i] = hits / len(local_rays)

    return occlusion_scores * occlusion_weight
