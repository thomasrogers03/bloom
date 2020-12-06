# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from ...map_data import wall
from .. import map_objects
from ..map_objects.drawing import sector as drawing_sector


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
