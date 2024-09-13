import os

import bpy
import bpy_extras
import mathutils
from bpy.app.handlers import persistent


def to_camera_space(world_position, camera):
    scene = bpy.context.scene
    co_2d = bpy_extras.object_utils.world_to_camera_view(scene, camera, world_position)
    render_scale = scene.render.resolution_percentage / 100
    render_size = (
        int(scene.render.resolution_x * render_scale),
        int(scene.render.resolution_y * render_scale),
    )
    pixel_coords = (
        round(co_2d.x * render_size[0]),
        round(render_size[1] - co_2d.y * render_size[1]),
    )
    return pixel_coords


def get_absolute_path(relative_path):
    blend_file_directory = bpy.path.abspath("//")
    full_path = os.path.join(blend_file_directory, relative_path.lstrip('//'))
    full_path = os.path.normpath(full_path)
    os.makedirs(full_path, exist_ok=True)
    return full_path


def is_projection_in_camera_view(x, y, camera_position):
    return (x >= camera_position[0] > 0 and
            y >= camera_position[1] > 0)


def count_persons_in_frame(camera, depsgraph, object_name, size_x, size_y):
    projections = []
    for object_instance in depsgraph.object_instances:
        obj = object_instance.object
        if object_instance.is_instance and object_instance.parent.name == object_name:
            world_position = object_instance.matrix_world.translation
            world_position = mathutils.Vector((world_position.x, world_position.y, obj.dimensions.z * 0.9))
            camera_position = to_camera_space(world_position, camera)
            if is_projection_in_camera_view(size_x, size_y, camera_position):
                projections.append(camera_position)
                # print(f"Instance of {obj.name} at world: {world_position} at camera: {camera_position}")
    return projections


class AnnotationProperties(bpy.types.PropertyGroup):
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

    only_annotation: bpy.props.BoolProperty(
        name="Only annotation",
        description="With this renders only annotation and skips cycles rendering",
        default=False
    )


class RenderOperator(bpy.types.Operator):
    """Render images with annotations"""
    bl_idname = "render.annotation"
    bl_label = "Render Annotations"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.custom_properties

        if not props.folder_path:
            self.report({'WARNING'}, "No folder path specified")
            return {'CANCELLED'}
        if not props.noded_object:
            self.report({'WARNING'}, "No Main Object set")
            return {'CANCELLED'}

        output_path = props.folder_path
        object_name = props.noded_object.name
        obj = bpy.data.objects[object_name]

        if not any(mod.type == 'NODES' for mod in obj.modifiers):
            self.report({'WARNING'}, "No Geo nodes found on {object_name}")
            return {'CANCELLED'}

        if not output_path.endswith('/'):
            output_path += '/'

        camera = bpy.context.scene.camera
        bpy.context.scene.render.image_settings.file_format = 'JPEG'
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj.evaluated_get(depsgraph)
        annotation_folder = get_absolute_path(os.path.join(output_path, "gt"))
        starting_frame = bpy.context.scene.frame_current

        render = bpy.context.scene.render
        scale = render.resolution_percentage / 100
        size_x = render.resolution_x * scale
        size_y = render.resolution_y * scale

        for i in range(props.renders_quantity):
            current_frame = bpy.context.scene.frame_current
            print(current_frame)

            if not props.only_annotation:
                bpy.context.scene.render.filepath = f"{output_path}img/IMG_{current_frame}.jpg"
                bpy.ops.render.render(write_still=True)
                self.report({'INFO'}, f"Rendered sequence saved to {output_path}img/IMG_{current_frame}.jpg")

            projections = count_persons_in_frame(camera, depsgraph, object_name, size_x, size_y)
            full_path = os.path.join(annotation_folder, f"GT_{current_frame}.txt")
            with open(full_path, 'a') as file:
                file.writelines(str(projections))

            bpy.context.scene.frame_current = bpy.context.scene.frame_current + 1

        self.report({'INFO'}, f"Process finished")
        bpy.context.scene.frame_current = starting_frame
        return {'FINISHED'}

    @persistent
    def decimate_addon_handler(scene):
        props = scene.custom_properties
        depsgraph = bpy.context.evaluated_depsgraph_get()
        props.noded_object.evaluated_get(depsgraph)

        render = bpy.context.scene.render
        scale = render.resolution_percentage / 100
        size_x = render.resolution_x * scale
        size_y = render.resolution_y * scale

        for o in scene.objects:
            if o.type == 'MESH':
                if "GeometryNodes" in o.modifiers:
                    count = count_persons_in_frame(scene.camera, depsgraph, props.noded_object.name, size_x, size_y)
                    props.crowd_to_render = len(count)

    bpy.app.handlers.frame_change_post.append(decimate_addon_handler)


class AnnotationPanel(bpy.types.Panel):
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

        # Allows to render only annotation
        row = layout.row()
        row.prop(props, "only_annotation")
        row.enabled = props.use_annotation

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


def register():
    bpy.utils.register_class(AnnotationProperties)
    bpy.types.Scene.custom_properties = bpy.props.PointerProperty(type=AnnotationProperties)
    bpy.utils.register_class(RenderOperator)
    bpy.utils.register_class(AnnotationPanel)


def unregister():
    bpy.utils.unregister_class(AnnotationPanel)
    bpy.utils.unregister_class(RenderOperator)
    del bpy.types.Scene.custom_properties
    bpy.utils.unregister_class(AnnotationProperties)


if __name__ == "__main__":
    register()
