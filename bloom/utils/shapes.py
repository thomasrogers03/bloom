# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import os.path

from panda3d import core

from .. import cameras, constants


def make_grid(
    camera_collection: cameras.Cameras,
    name: str,
    thickness: float,
    line_count: int,
    colour: core.Vec4,
):
    cache_path = f"bloom/pre_cache/{name}.bam"
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


def make_z_grid(
    camera_collection: cameras.Cameras,
    name: str,
    thickness: float,
    segment_count: int,
    colour: core.Vec4,
):
    cache_path = f"bloom/pre_cache/vertical_{name}.bam"
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


def align_grid_to_angle(
    scene: core.NodePath, grid: core.NodePath, grid_size: float, slope: core.Vec2
):
    grid.set_hpr(0, slope.y, slope.x)
    grid.set_scale(1)
    inverse_scale = scene.get_relative_vector(grid, core.Vec3(1, 1, 0))
    grid.set_scale(grid_size / inverse_scale.x, grid_size / inverse_scale.y, 1)


def make_circle(
    scene: core.NodePath, position: core.Point3, radius: float, point_count: int
):
    vertex_data = _make_vertex_data(point_count)
    position_writer = core.GeomVertexWriter(vertex_data, "vertex")
    colour_writer = core.GeomVertexWriter(vertex_data, "color")

    for index in range(point_count):
        theta = (2 * math.pi * index) / point_count
        x = math.cos(theta) * radius
        y = math.sin(theta) * radius

        position_writer.add_data3(position.x + x, position.y + y, position.z)
        colour_writer.add_data4(1, 1, 1, 1)

    primitive = core.GeomTriangles(core.Geom.UH_static)
    for index in range(1, point_count + 1):
        point_2 = (index + 1) % point_count
        point_3 = (index + 2) % point_count
        primitive.add_vertices(0, point_2, point_3)
    primitive.close_primitive()

    geometry = core.Geom(vertex_data)
    geometry.add_primitive(primitive)

    geometry_node = core.GeomNode("circle")
    geometry_node.add_geom(geometry)

    result: core.NodePath = scene.attach_new_node(geometry_node)
    result.set_two_sided(True)
    result.set_transparency(True)

    return result


def make_arc(
    scene: core.NodePath,
    position: core.Point3,
    radius: float,
    theta_degrees: float,
    point_count: int,
):
    theta_radians = math.radians(theta_degrees)
    vertex_data = _make_vertex_data(point_count + 1)
    position_writer = core.GeomVertexWriter(vertex_data, "vertex")
    colour_writer = core.GeomVertexWriter(vertex_data, "color")

    position_writer.add_data3(position.x, position.y, position.z)
    colour_writer.add_data4(1, 1, 1, 1)

    for index in range(point_count):
        theta = (theta_radians * index) / (point_count - 1)
        x = math.cos(theta) * radius
        y = math.sin(theta) * radius

        position_writer.add_data3(position.x + x, position.y + y, position.z)
        colour_writer.add_data4(1, 1, 1, 1)

    primitive = core.GeomTriangles(core.Geom.UH_static)
    total_point_count = point_count + 1
    for index in range(point_count):
        point_2 = (index + 1) % total_point_count
        point_3 = (index + 2) % total_point_count
        primitive.add_vertices(0, point_2, point_3)
    primitive.close_primitive()

    geometry = core.Geom(vertex_data)
    geometry.add_primitive(primitive)

    geometry_node = core.GeomNode("arc")
    geometry_node.add_geom(geometry)

    result: core.NodePath = scene.attach_new_node(geometry_node)
    result.set_two_sided(True)
    result.set_transparency(True)

    return result


def _make_vertex_data(vertex_count: int):
    vertex_data = core.GeomVertexData(
        "shape", constants.VERTEX_FORMAT, core.Geom.UH_static
    )
    vertex_data.set_num_rows(vertex_count)
    return vertex_data
