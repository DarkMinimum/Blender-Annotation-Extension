import bpy

from .context_properties import ContextProperties
from .render_operator import RenderOperator
from .ui_camera_panel import UiPanel


def register():
    bpy.utils.register_class(ContextProperties)
    bpy.types.Scene.custom_properties = bpy.props.PointerProperty(type=ContextProperties)
    bpy.utils.register_class(RenderOperator)
    bpy.utils.register_class(UiPanel)


def unregister():
    bpy.utils.unregister_class(UiPanel)
    bpy.utils.unregister_class(RenderOperator)
    del bpy.types.Scene.custom_properties
    bpy.utils.unregister_class(ContextProperties)


if __name__ == "__main__":
    register()
