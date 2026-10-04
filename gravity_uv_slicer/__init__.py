bl_info = {
    "name": "Gravity UV Slicer",
    "author": "Antigravity & Developer",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),  # Совместимо с 4.x и 5.x
    "location": "View3D > Sidebar > Gravity UV Slicer",
    "description": "Автоматическая нарезка UV-швов с учетом гравитации и слепых зон",
    "warning": "",
    "doc_url": "",
    "category": "UV",
}

import bpy
import sys
import importlib

# Автоматическое обновление модулей при перезапуске плагина (Hot Reload)
if "properties" in locals():
    importlib.reload(properties)
if "ui" in locals():
    importlib.reload(ui)
if "operators" in locals():
    importlib.reload(operators)
if "core" in locals():
    # Находим и перезагружаем все подмодули ядра (geometry, flow, occlusion, slicer, overlay)
    for name in list(sys.modules.keys()):
        if name.startswith(__name__ + ".core"):
            importlib.reload(sys.modules[name])

# Импортируем модули плагина
from . import properties
from . import ui
from . import operators
from .core import overlay

def register():
    properties.register()
    ui.register()
    operators.register()
    overlay.register()

def unregister():
    overlay.unregister()
    operators.unregister()
    ui.unregister()
    properties.unregister()

if __name__ == "__main__":
    register()
