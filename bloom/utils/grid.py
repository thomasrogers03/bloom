# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import os.path

from panda3d import core

from .. import cameras


def make_grid(camera_collection: cameras.Cameras, name: str, thickness: float, line_count: int, colour: core.Vec4):
    cache_path = f'cache/{name}.bam'
    if os.path.exists(cache_path):
        return camera_collection.load_model_into_scene(cache_path)

    grid_node = core.GeomNode(name)
    grid: core.NodePath = camera_collection.scene.attach_new_node(grid_node)

    half_line_count = int(line_count / 2)
    for x in range(line_count):
        for y in range(line_count):
            cell_segments = core.LineSegs()
            cell_segments.set_thickness(thickness)
            cell_segments.set_color(colour)

            offset_x = x - half_line_count
            offset_y = y - half_line_count

            cell_segments.draw_to(offset_x, offset_y, 0)
            cell_segments.draw_to(offset_x, offset_y + 1, 0)
            cell_segments.draw_to(offset_x + 1, offset_y + 1, 0)
            cell_segments.draw_to(offset_x + 1, offset_y, 0)
            cell_segments.draw_to(offset_x, offset_y, 0)

            cell_segments.create(grid_node)

    grid.flatten_strong()
    grid.set_transparency(True)

    grid.write_bam_file(cache_path)

    return grid
