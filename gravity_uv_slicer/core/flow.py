import numpy as np

def compute_flow_and_gravity(geometry, settings):
    """
    Рассчитывает направления течения воды (гравитации) по полигонам
    и вычисляет оценки для каждого ребра:
    1. Бонус за водоразделы (где потеки расходятся).
    2. Штраф за пересечение вертикальных трасс (горизонтальные разрезы).
    """
    num_faces = geometry.num_faces
    num_edges = geometry.num_edges
    
    # Вектор силы тяжести направлен строго вниз по оси Z
    gravity = np.array([0.0, 0.0, -1.0])
    
    # 1. Расчет векторов течения для каждого полигона
    # Проецируем гравитацию на плоскость полигона: V = G - (G * N) * N
    dot_n_g = np.dot(geometry.face_normals_world, gravity)  # скалярное произведение для каждого лица
    
    # Проекция вектора гравитации
    flow_vectors = np.zeros((num_faces, 3))
    for i in range(num_faces):
        n = geometry.face_normals_world[i]
        flow_vectors[i] = gravity - dot_n_g[i] * n
        
    # Нормализуем векторы течения
    flow_norms = np.linalg.norm(flow_vectors, axis=1, keepdims=True)
    flow_dirs = np.divide(flow_vectors, flow_norms, 
                          out=np.zeros_like(flow_vectors), 
                          where=flow_norms > 1e-5)

    # Инициализируем массивы для оценок ребер
    watershed_bonus = np.zeros(num_edges)
    vertical_penalty = np.zeros(num_edges)
    
    # 2. Обход ребер для расчета оценок
    for i in range(num_edges):
        connected_faces = geometry.edge_to_faces[i]
        edge_center = geometry.edge_centers_world[i]
        edge_dir = geometry.edge_dirs_world[i]
        
        if len(connected_faces) == 2:
            face_a, face_b = connected_faces
            
            # Векторы течения на соседних полигонах
            v_a = flow_dirs[face_a]
            v_b = flow_dirs[face_b]
            
            # --- РАСЧЕТ ВОДОРАЗДЕЛА (Где потеки разделяются) ---
            # Векторы от центра ребра к центрам полигонов
            dir_to_a = geometry.face_centers_world[face_a] - edge_center
            dir_to_b = geometry.face_centers_world[face_b] - edge_center
            
            # Нормализуем направления к полигонам
            norm_a = np.linalg.norm(dir_to_a)
            norm_b = np.linalg.norm(dir_to_b)
            
            if norm_a > 1e-5 and norm_b > 1e-5:
                dir_to_a /= norm_a
                dir_to_b /= norm_b
                
                # Если вектор течения совпадает с направлением к полигону,
                # значит вода течет ОТ ребра в сторону полигона.
                flow_away_a = np.dot(v_a, dir_to_a)
                flow_away_b = np.dot(v_b, dir_to_b)
                
                # Если с обеих сторон вода течет от ребра, это водораздел!
                if flow_away_a > 0.1 and flow_away_b > 0.1:
                    watershed_bonus[i] = flow_away_a + flow_away_b
            
            # --- РАСЧЕТ ЗАЩИТЫ ВЕРТИКАЛЕЙ ---
            # Находим средний вектор течения на этом ребре
            v_avg = (v_a + v_b) * 0.5
            v_avg_norm = np.linalg.norm(v_avg)
            if v_avg_norm > 1e-5:
                v_avg /= v_avg_norm
                
                # Насколько направление ребра совпадает с течением воды
                # Если ребро параллельно течению (вертикальное), то |dot| = 1.0. Штраф = 0.
                # Если ребро перпендикулярно течению (горизонтальное), то |dot| = 0.0. Штраф = 1.0.
                alignment = abs(np.dot(edge_dir, v_avg))
                vertical_penalty[i] = 1.0 - alignment
                
        elif len(connected_faces) == 1:
            # Граничные ребра (например, низ стены или край открытой геометрии)
            # Их можно резать легче, так как это край модели
            face_a = connected_faces[0]
            v_a = flow_dirs[face_a]
            v_a_norm = np.linalg.norm(v_a)
            
            if v_a_norm > 1e-5:
                v_a_normalized = v_a / v_a_norm
                alignment = abs(np.dot(edge_dir, v_a_normalized))
                vertical_penalty[i] = 1.0 - alignment
            
    # Умножаем результаты на веса из настроек
    gravity_weight = settings.gravity_weight
    vertical_weight = settings.vertical_protection
    
    return watershed_bonus * gravity_weight, vertical_penalty * vertical_weight
