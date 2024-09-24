import bpy
import bpy_extras

image_mist_path = r"D:\diplomaWork\datasets\generated\depth\Mist0001.jpg"
image_custom_exr_path = r"D:\diplomaWork\datasets\generated\depth\Image Custom0001.exr"


def get_mist(x, y):
    """
    Returns value of Mist map of pixel by hardcoded path
    :param x:
    :param y:
    :return: values in range of [0;1]
    """
    image = bpy.data.images.load(image_mist_path)
    width, height = image.size[0], image.size[1]
    pixels = image.pixels

    # Flip the Y-coordinate to account for bottom-left origin in pixel space
    flipped_y = height - y

    pixel_index = (flipped_y * width + x) * 4
    r = pixels[pixel_index]
    print(f"\tmist value: {r}")
    return r


def get_exr_pixel(x, y):
    """
    Returns value of Z buffer for pixel by hardcoded path
    :param x:
    :param y:
    :return: measured in meters
    """
    image = bpy.data.images.load(image_custom_exr_path)
    width, height = image.size[0], image.size[1]
    pixels = image.pixels

    # Flip the Y-coordinate to account for bottom-left origin in pixel space
    flipped_y = height - y

    pixel_index = (flipped_y * width + x) * 4
    r = pixels[pixel_index]
    print(f"\texr value: {r}")
    return r


def get_object_distance_from_camera(camera, obj):
    """
    Calculate the distance of the object from the camera using the object's origin point.
    Returns the distance in world units.
    """
    obj_location = obj.matrix_world.translation
    scene = bpy.context.scene
    co_2d = bpy_extras.object_utils.world_to_camera_view(scene, camera, obj_location)

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
    print(f"({pixel_coords[0]}:{pixel_coords[1]})")
    print(f"\treal value: {pixel_coords[2]}")

    return pixel_coords


def iterate_objects_and_get_distances():
    """
    Iterate over all objects in the scene and calculate the distance from the active camera.
    """
    scene = bpy.context.scene
    camera = scene.camera

    if camera is None:
        print("No active camera found in the scene.")
        return

    for obj in scene.objects:
        if obj == camera or not obj.type == 'MESH':
            continue

        print(obj.name)
        coords = get_object_distance_from_camera(camera, obj)
        get_mist(coords[0], coords[1])
        get_exr_pixel(coords[0], coords[1])


iterate_objects_and_get_distances()
