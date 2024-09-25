import os

import bpy
import bpy_extras
import mathutils
from bpy.app.handlers import persistent

from .context_properties import ContextProperties
from .ui_camera_panel import UiPanel

# helps to scale vertical position of the head point
height_coef = 0.935
# helps tolerate error during comperashion of mesh surface and origin point of head
depth_error = 0.5


def to_camera_space(world_position, camera):
    """Translates world position (X;Y;Z) to camera position (X;Y) and returns the depth (Z)"""
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
        co_2d.z
    )
    return pixel_coords


def get_absolute_path(relative_path):
    blend_file_directory = bpy.path.abspath("//")
    full_path = os.path.join(blend_file_directory, relative_path.lstrip('//'))
    full_path = os.path.normpath(full_path)
    os.makedirs(full_path, exist_ok=True)
    return full_path


def is_projection_in_camera_view(x, y, camera_position):
    """Checks if point lies in camera boundaries"""
    return (x >= camera_position[0] > 0 and
            y >= camera_position[1] > 0)


def count_persons_in_frame(camera, depsgraph, object_name, size_x, size_y,
                           parent=None, is_render=False,
                           reduce_occluded=False, is_debug=False, frame=0):
    """Counts array of points in camera view"""
    if parent is None:
        parent = {}
    projections = []
    for object_instance in depsgraph.object_instances:
        obj = object_instance.object
        if object_instance.is_instance and object_instance.parent.name == object_name:
            world_position = object_instance.matrix_world.translation
            world_position = mathutils.Vector((world_position.x, world_position.y, obj.dimensions.z * height_coef))
            object_in_camera_position = to_camera_space(world_position, camera)
            if is_projection_in_camera_view(size_x, size_y, object_in_camera_position):
                projections.append(object_in_camera_position)
                if is_debug:
                    print(f"Instance of {obj.name} at world: {world_position} at camera: {object_in_camera_position}")

    if is_render and reduce_occluded:
        if bpy.context.scene.use_nodes:
            pixels = bpy.data.images['Viewer Node'].pixels
            filtered_projection = filter_occluded_heads(projections, pixels, is_debug)
            if is_debug:
                print(
                    "Frame: %d Initial quantity: %d, reduced to: %d" % (
                        frame, len(projections), len(filtered_projection)))
            projections = filtered_projection
        else:
            parent.report({'WARNING'}, "Please set up Viewer Node with Z-Path in order to filter by depth")

    reduced_projections = [coords[:2] for coords in projections]
    return reduced_projections


def filter_occluded_heads(projections, pixels, is_debug=False):
    visible_heads = []
    width = bpy.context.scene.render.resolution_x
    height = bpy.context.scene.render.resolution_y

    for projection in projections:
        x_pixel, y_pixel, head_depth = int(projection[0]), int(projection[1]), projection[2]
        if 0 <= x_pixel < width and 0 <= y_pixel < height:

            flipped_y = height - y_pixel
            pixel_index = (flipped_y * width + x_pixel) * 4
            buffer_depth = pixels[pixel_index]
            if is_debug:
                print("(%d:%d)\t" % (x_pixel, y_pixel) +
                      "{:.5f}".format(head_depth) + " < " +
                      "{:.5f}".format(buffer_depth) + " : " +
                      "{:.5f}".format(head_depth - buffer_depth))

            if head_depth - buffer_depth < depth_error:
                visible_heads.append(projection)

    return visible_heads


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
            depsgraph.update()
            bpy.context.scene.render.filepath = f"{output_path}img/IMG_{current_frame}.jpg"
            bpy.ops.render.render(write_still=True)
            self.report({'INFO'}, f"Rendered sequence saved to {output_path}img/IMG_{current_frame}.jpg")
            projections = count_persons_in_frame(camera, depsgraph, object_name, size_x, size_y, self,
                                                 True, props.filter_occluded_points, props.log_debug, i)
            full_path = os.path.join(annotation_folder, f"GT_{current_frame}.txt")
            with open(full_path, 'a') as file:
                file.writelines(str(projections))

            bpy.context.scene.frame_current += 1

        self.report({'INFO'}, f"Process finished")
        bpy.context.scene.frame_current = starting_frame
        return {'FINISHED'}

    @persistent
    def on_frame_changed(scene):
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

    bpy.app.handlers.frame_change_post.append(on_frame_changed)
    bpy.app.handlers.depsgraph_update_post.append(on_frame_changed)


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
