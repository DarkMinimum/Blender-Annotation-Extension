import os
from datetime import datetime

import bpy
from bpy.app.handlers import persistent

from .utils import get_absolute_path, count_persons_in_frame


def generate_meta(camera, depsgraph, output_path, props, size_x, size_y):
    meta_folder = get_absolute_path(os.path.join(output_path, "meta"))
    date = str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
    full_path = os.path.join(meta_folder, f"meta_{date.replace(':', '_')}.txt")
    with open(full_path, 'a') as file:
        persons_in_frame = count_persons_in_frame(camera, depsgraph, size_x, size_y, props)
        file.writelines(date + '\n')
        file.writelines('Occlusion error: ' + str(props.occlusion_error) + '\n')
        file.writelines('Quantity of people before filtering: ' + str(len(persons_in_frame)) + '\n')
        file.writelines('Quantity of frames: ' + str(props.renders_quantity) + '\n')


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
        obj = bpy.data.objects[props.noded_object.name]

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

        generate_meta(camera, depsgraph, output_path, props, size_x, size_y)

        for i in range(props.renders_quantity):
            current_frame = bpy.context.scene.frame_current
            depsgraph.update()
            bpy.context.scene.render.filepath = f"{output_path}img/IMG_{current_frame}.jpg"
            bpy.ops.render.render(write_still=True)
            self.report({'INFO'}, f"Rendered sequence saved to {output_path}img/IMG_{current_frame}.jpg")
            projections = count_persons_in_frame(camera, depsgraph, size_x, size_y, props, self,
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
        """
        Handler for the real-time counter of crowd in camera frame
        """
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
                    count = count_persons_in_frame(scene.camera, depsgraph, size_x, size_y, props)
                    props.crowd_to_render = len(count)

    bpy.app.handlers.frame_change_post.append(on_frame_changed)
    bpy.app.handlers.depsgraph_update_post.append(on_frame_changed)
