import os

import bpy
import bpy_extras
import mathutils

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
