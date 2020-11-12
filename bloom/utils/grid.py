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

def make_z_grid(camera_collection: cameras.Cameras, name: str, thickness: float, segment_count: int, colour: core.Vec4):
    cache_path = f'cache/vertical_{name}.bam'
    if os.path.exists(cache_path):
        return camera_collection.load_model_into_scene(cache_path)

    grid_node = core.GeomNode(name)
    grid: core.NodePath = camera_collection.scene.attach_new_node(grid_node)

    half_segment_count = int(segment_count / 2)

    cell_segments = core.LineSegs()
    cell_segments.set_thickness(thickness)
    cell_segments.set_color(colour)

    cell_segments.draw_to(0, 0, -half_segment_count)
    cell_segments.draw_to(0, 0, half_segment_count)
    cell_segments.create(grid_node)

    for z in range(segment_count):
        cell_segments = core.LineSegs()
        cell_segments.set_thickness(thickness)
        cell_segments.set_color(colour)

        offset = z - half_segment_count

        cell_segments.draw_to(-0.125, -0.125, offset)
        cell_segments.draw_to(-0.125, 0.125, offset)
        cell_segments.draw_to(0.125, 0.125, offset)
        cell_segments.draw_to(0.125, -0.125, offset)
        cell_segments.draw_to(-0.125, -0.125, offset)

        cell_segments.create(grid_node)

    grid.flatten_strong()
    grid.set_transparency(True)

    grid.write_bam_file(cache_path)

    return grid

def angle_grid(
    camera_collection: cameras.Cameras, 
    grid: core.NodePath,
    grid_size: float, 
    slope: core.Vec2
):
    grid.set_hpr(
        0,
        slope.y,
        slope.x
    )
    grid.set_scale(1)
    inverse_scale = camera_collection.scene.get_relative_vector(grid, core.Vec3(1, 1, 0))
    grid.set_scale(
        grid_size / inverse_scale.x,
        grid_size / inverse_scale.y,
        1
    )
