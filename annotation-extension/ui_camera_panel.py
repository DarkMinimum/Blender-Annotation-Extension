import bpy


class UiPanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Annotation"
    bl_idname = "OBJECT_PT_Annotation"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    def draw_header(self, context):
        self.layout.prop(context.scene.custom_properties, "use_annotation", text="")

    def draw(self, context):
        layout = self.layout
        props = context.scene.custom_properties
        obj = context.object

        # Current camera name
        row = layout.row()
        row.label(text="Current camera object: " + obj.name)
        row.enabled = props.use_annotation

        # Number of people in one frame
        row = layout.row()
        row.label(text="Number of people in frame: " + str(props.crowd_to_render))
        row.enabled = props.use_annotation

        # Allows to reduce occluded points
        row = layout.row()
        row.prop(props, "filter_occluded_points")
        row.enabled = props.use_annotation

        # Allows to draw additional logs to Console
        row = layout.row()
        row.prop(props, "log_debug")
        row.enabled = props.use_annotation and props.filter_occluded_points

        # Object with node setup
        row = layout.row()
        row.prop(props, "noded_object")
        row.enabled = props.use_annotation

        # Export folder
        row = layout.row()
        row.prop(props, "folder_path", text="Export folder path")
        row.enabled = props.use_annotation

        # Quantity of frames to render
        row = layout.row()
        row.prop(props, "renders_quantity")
        row.enabled = props.use_annotation

        # Render button
        row = layout.row()
        row.operator("render.annotation", text="Render Frames With Annotations")
        row.enabled = props.use_annotation
