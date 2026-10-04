import bpy
from .core import slicer

class OBJECT_OT_gravity_uv_slice(bpy.types.Operator):
    bl_idname = "object.gravity_uv_slice"
    bl_label = "Gravity UV Slice"
    bl_description = "Разметить швы на основе гравитации и видимости для выбранных мешей"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Оператор активен, если выделен хотя бы один полигональный объект (Mesh)
        return any(obj.type == 'MESH' for obj in context.selected_objects)

    def execute(self, context):
        settings = context.scene.gravity_uv_slicer
        # Выбираем только полигональные объекты из выделенных
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not mesh_objects:
            self.report({'WARNING'}, "Нет выделенных полигональных объектов (Mesh)!")
            return {'CANCELLED'}
            
        success_count = 0
        original_active = context.active_object
        
        for obj in mesh_objects:
            # Делаем меш активным перед запуском
            context.view_layer.objects.active = obj
            success = slicer.slice_mesh(obj, settings)
            if success:
                success_count += 1
                obj.data.update()
                
        # Возвращаем исходный активный объект
        if original_active and original_active.name in context.scene.objects:
            context.view_layer.objects.active = original_active
            
        if success_count > 0:
            self.report({'INFO'}, f"Швы успешно размечены для {success_count} объектов!")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Не удалось разметить швы ни для одного объекта.")
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(OBJECT_OT_gravity_uv_slice)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_gravity_uv_slice)
