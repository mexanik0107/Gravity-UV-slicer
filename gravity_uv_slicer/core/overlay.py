import bpy
import gpu
from gpu_extras.batch import batch_for_shader

_handle = None
_seams_cache = []
_last_selection_hash = None

def draw_callback(dummy):
    global _seams_cache, _last_selection_hash
    context = bpy.context
    
    # 1. Проверяем, включен ли плагин и активирована ли галочка показа швов
    try:
        settings = context.scene.gravity_uv_slicer
    except AttributeError:
        return
        
    if not settings.show_overlay:
        return
        
    # 2. Быстрая проверка изменений (выделение, перемещение, поворот объектов)
    selected_meshes = [o for o in context.selected_objects if o.type == 'MESH']
    
    state_tuples = []
    for o in selected_meshes:
        matrix_tuple = tuple(tuple(row) for row in o.matrix_world)
        state_tuples.append((o.name, matrix_tuple))
    selection_hash = hash(tuple(state_tuples))
    
    if selection_hash != _last_selection_hash:
        update_seams_cache(selected_meshes)
        _last_selection_hash = selection_hash
        
    if not _seams_cache:
        return
        
    # 3. Отрисовка линий в 3D-вьюпорте
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    
    # Устанавливаем толщину линий в 3 пикселя
    try:
        gpu.state.line_width_set(3.0)
    except Exception:
        pass
    
    # Включаем тест глубины для отрисовки поверх модели
    gpu.state.depth_test_set('LESS_EQUAL')
    
    # Создаем буфер для отрисовки
    batch = batch_for_shader(shader, 'LINES', {"pos": _seams_cache})
    
    shader.bind()
    # Связываем матрицы проекции камеры вьюпорта с шейдером
    matrix = gpu.matrix.get_projection_matrix() @ gpu.matrix.get_model_view_matrix()
    shader.uniform_mat4("ModelViewProjectionMatrix", matrix)
    
    # Задаем яркий красный цвет для швов (RGBA)
    shader.uniform_float("color", (1.0, 0.0, 0.0, 1.0))
    batch.draw(shader)
    
    # КРИТИЧНО ДЛЯ BLENDER: Восстанавливаем глубину и толщину линий в исходное состояние,
    # иначе это сломает рендеринг самого Blender (модели станут прозрачными/рендеринг сломается)
    gpu.state.depth_test_set('NONE')
    try:
        gpu.state.line_width_set(1.0)
    except Exception:
        pass

def update_seams_cache(objects):
    """
    Быстро извлекает мировые координаты всех ребер со швами.
    Использует кэширование, чтобы не перегружать процессор при каждом кадре вьюпорта.
    """
    global _seams_cache
    _seams_cache = []
    
    for obj in objects:
        matrix = obj.matrix_world
        mesh = obj.data
        
        count = 0
        for edge in mesh.edges:
            if edge.use_seam:
                v1 = matrix @ mesh.vertices[edge.vertices[0]].co
                v2 = matrix @ mesh.vertices[edge.vertices[1]].co
                # Добавляем начальную и конечную точку отрезка
                _seams_cache.append((v1[0], v1[1], v1[2]))
                _seams_cache.append((v2[0], v2[1], v2[2]))
                count += 1
        print(f"[Gravity UV] Обновлен кэш швов для {obj.name}: найдено {count} швов.")

def register():
    global _handle
    if _handle is None:
        # Передаем None вместо bpy.context во время регистрации,
        # так как контекст при регистрации замораживается и становится недействительным.
        # Внутри draw_callback мы будем брать актуальный динамический bpy.context.
        _handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback, (None,), 'WINDOW', 'POST_VIEW')

def unregister():
    global _handle
    if _handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
