import bpy
import bmesh
import numpy as np

class MeshGeometry:
    def __init__(self, obj):
        """
        Собирает геометрические данные модели и переводит их в матрицы NumPy.
        Все расчеты переводим в мировое пространство (World Space),
        так как сила тяжести действует глобально.
        """
        self.obj = obj
        self.mesh = obj.data
        
        # Получаем матрицу трансформации объекта в мировые координаты
        self.matrix_world = np.array(obj.matrix_world)
        self.matrix_rotation = np.array(obj.matrix_world.to_3x3())
        
        # Создаем BMesh для удобного обхода топологии
        self.bm = bmesh.new()
        self.bm.from_mesh(self.mesh)
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()
        self.bm.verts.ensure_lookup_table()
        
        self.num_faces = len(self.bm.faces)
        self.num_edges = len(self.bm.edges)
        
        self.collect_data()

    def collect_data(self):
        # 1. Сбор нормалей полигонов в мировых координатах
        # Каждая нормаль - это вектор направления лица полигона
        local_normals = np.array([f.normal for f in self.bm.faces])
        # Умножаем локальные нормали на матрицу вращения объекта
        self.face_normals_world = local_normals @ self.matrix_rotation.T
        # Нормализуем векторы
        norms = np.linalg.norm(self.face_normals_world, axis=1, keepdims=True)
        self.face_normals_world = np.divide(self.face_normals_world, norms, 
                                            out=np.zeros_like(self.face_normals_world), 
                                            where=norms > 1e-6)

        # 2. Сбор центров полигонов в мировых координатах
        local_centers = np.array([f.calc_center_bounds() for f in self.bm.faces])
        # Переводим центры в мировые координаты
        ones = np.ones((self.num_faces, 1))
        local_centers_4d = np.hstack((local_centers, ones))
        self.face_centers_world = (local_centers_4d @ self.matrix_world.T)[:, :3]

        # 3. Информация о ребрах
        # Для каждого ребра нам нужны:
        # - Индексы связанных полигонов
        # - Вектор самого ребра в мировых координатах
        # - Центр ребра в мировых координатах (для пуска лучей)
        self.edge_to_faces = []      # Список пар индексов полигонов для каждого ребра
        self.edge_vectors_world = np.zeros((self.num_edges, 3))
        self.edge_centers_world = np.zeros((self.num_edges, 3))
        
        for i, edge in enumerate(self.bm.edges):
            # Связанные полигоны (обычно 2 для внутренних ребер, 1 для границ)
            connected_faces = [f.index for f in edge.link_faces]
            self.edge_to_faces.append(connected_faces)
            
            # Координаты вершин ребра в мировом пространстве
            v1_world = np.array(self.obj.matrix_world @ edge.verts[0].co)
            v2_world = np.array(self.obj.matrix_world @ edge.verts[1].co)
            
            self.edge_vectors_world[i] = v2_world - v1_world
            self.edge_centers_world[i] = (v1_world + v2_world) * 0.5
            
        # Нормализуем векторы ребер
        edge_norms = np.linalg.norm(self.edge_vectors_world, axis=1, keepdims=True)
        self.edge_dirs_world = np.divide(self.edge_vectors_world, edge_norms, 
                                         out=np.zeros_like(self.edge_vectors_world), 
                                         where=edge_norms > 1e-6)

    def free(self):
        """Очистка BMesh из памяти"""
        self.bm.free()
