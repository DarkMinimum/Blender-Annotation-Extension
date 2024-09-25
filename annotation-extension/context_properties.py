import bpy


class ContextProperties(bpy.types.PropertyGroup):
    """
    Context of the extension, allows to share data between UI and RenderOperator
    """
    use_annotation: bpy.props.BoolProperty(
        name="Enable Annotation",
        description="This menu enables to create image annotations",
        default=False
    )

    folder_path: bpy.props.StringProperty(
        name="Folder Path",
        description="Path to a folder with renders and annotations",
        subtype='DIR_PATH'
    )

    renders_quantity: bpy.props.IntProperty(
        name="Renders Quantity",
        description="Number of renders that would be generated",
        default=1,
        min=1
    )

    noded_object: bpy.props.PointerProperty(
        name="Main Object",
        type=bpy.types.Object,
        description="Object with Geometry Nodes setup"
    )

    crowd_to_render: bpy.props.IntProperty(
        name="Renders Quantity",
        description="Number of head that will be annotated",
        default=0,
        min=0
    )

    filter_occluded_points: bpy.props.BoolProperty(
        name="Filter occluded points",
        description="Reduce points that are hidden behind meshes",
        default=True
    )

    log_debug: bpy.props.BoolProperty(
        name="Console logging",
        description="Shows stats of reduced points and generating process",
        default=False
    )
