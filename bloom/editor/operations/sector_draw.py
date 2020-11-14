# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from ...map_data import wall
from .. import map_objects


def are_points_clockwise(points: typing.List[core.Point2]):
    winding = 0
    segments = zip(points, (points[1:] + points[:1]))
    for point_1, point_2 in segments:
        winding += (point_2.x - point_1.x) * (point_2.y + point_1.y)

    return winding > 0

def is_sector_section_clockwise(start_wall: map_objects.EditorWall):
    points = get_wall_bunch_points(start_wall)
    return are_points_clockwise(points)

def get_wall_bunch_points(start_wall: map_objects.EditorWall):
    points: typing.List[core.Point2] = []
    current_wall = start_wall.wall_point_2
    
    while current_wall != start_wall:
        points.append(current_wall.point_1)
        current_wall = current_wall.wall_point_2
    points.append(current_wall.point_1)

    return points

def make_wall_points(
    blood_wall_base: wall.Wall,
    editor_sector: map_objects.EditorSector,
    points: typing.List[core.Vec2]
) -> typing.List[map_objects.EditorWall]:
    result: typing.List[map_objects.EditorWall] = []
    for point in points:
        new_blood_wall = blood_wall_base.copy()
        new_blood_wall.wall.position_x = int(point.x)
        new_blood_wall.wall.position_y = int(point.y)

        new_wall = editor_sector.add_wall(new_blood_wall)
        result.append(new_wall)
    return result

def find_wall_on_point(sector: map_objects.EditorSector, point: core.Point2):
    for wall in sector.walls:
        if wall.point_1 == point:
            return wall

    return None