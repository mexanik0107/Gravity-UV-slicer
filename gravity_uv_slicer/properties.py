import bpy

class GravityUVSlicerSettings(bpy.types.PropertyGroup):
    threshold_angle: bpy.props.FloatProperty(
        name="Допуск деформации",
        description="Разрешить растяжение UV на этот угол ради сохранения непрерывности (в градусах)",
        default=30.0,
        min=0.0,
        max=90.0
    )
    
    gravity_weight: bpy.props.FloatProperty(
        name="Влияние гравитации",
        description="Приоритет разреза на водоразделах (где потеки расходятся)",
        default=0.5,
        min=0.0,
        max=1.0
    )
    
    vertical_protection: bpy.props.FloatProperty(
        name="Защита вертикалей",
        description="Штраф за горизонтальные разрезы на путях стекания воды",
        default=0.8,
        min=0.0,
        max=1.0
    )
    
    occlusion_weight: bpy.props.FloatProperty(
        name="Влияние скрытых зон",
        description="Приоритет размещения швов в затененных нишах и углах",
        default=0.5,
        min=0.0,
        max=1.0
    )
    
    show_overlay: bpy.props.BoolProperty(
        name="Показать швы",
        description="Подсветить швы яркими красными линиями во вьюпорте",
        default=False
    )

def register():
    bpy.utils.register_class(GravityUVSlicerSettings)
    bpy.types.Scene.gravity_uv_slicer = bpy.props.PointerProperty(type=GravityUVSlicerSettings)

def unregister():
    del bpy.types.Scene.gravity_uv_slicer
    bpy.utils.unregister_class(GravityUVSlicerSettings)
