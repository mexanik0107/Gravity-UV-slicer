import bpy

class VIEW3D_PT_gravity_uv_slicer(bpy.types.Panel):
    bl_label = "Gravity UV Slicer"
    bl_idname = "VIEW3D_PT_gravity_uv_slicer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gravity UV'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        settings = scene.gravity_uv_slicer

        # Блок настроек
        col = layout.column(align=True)
        col.label(text="Настройки разметки швов:")
        col.prop(settings, "threshold_angle", text="Допуск угла")
        col.prop(settings, "gravity_weight", text="Вес гравитации")
        col.prop(settings, "vertical_protection", text="Защита вертикалей")
        col.prop(settings, "occlusion_weight", text="Скрытые зоны")

        layout.separator()
        
        # Визуализация швов
        col_vis = layout.column(align=True)
        col_vis.prop(settings, "show_overlay", text="Подсветить швы красным", icon='HIDE_OFF')

        layout.separator()

        # Кнопка действия
        layout.operator("object.gravity_uv_slice", text="Нарезать швы", icon='UV_DATA')

def register():
    bpy.utils.register_class(VIEW3D_PT_gravity_uv_slicer)

def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_gravity_uv_slicer)
