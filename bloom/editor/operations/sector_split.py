# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects


class SectorSplit:

    def __init__(self, sector_to_split: map_objects.EditorSector):
        self._sector_to_split = sector_to_split

    def split(
        self,
        points: typing.List[core.Point2]
    ):
        if len(points) < 3:
            return

        new_sector = self._sector_to_split.new_sector()
        angles = zip(points, (points[1:] + points[:1]))
        winding = 0
        for point_1, point_2 in angles:
            winding += (point_2.x - point_1.x) * (point_2.y + point_1.y)

        if winding > 0:
            reversed_points = reversed(points)
        else:
            reversed_points = points
            points = reversed(points)

        wall_base = self._sector_to_split.walls[0].blood_wall

        new_walls: typing.List[map_objects.EditorWall] = []
        for point in points:
            new_blood_wall = wall_base.copy()
            new_blood_wall.wall.position_x = int(point.x)
            new_blood_wall.wall.position_y = int(point.y)

            new_wall = self._sector_to_split.add_wall(new_blood_wall)
            new_walls.append(new_wall)

        new_otherside_walls: typing.List[map_objects.EditorWall] = []
        for point in reversed_points:
            new_blood_wall = wall_base.copy()
            new_blood_wall.wall.position_x = int(point.x)
            new_blood_wall.wall.position_y = int(point.y)

            new_wall = new_sector.add_wall(new_blood_wall)
            new_otherside_walls.append(new_wall)

        otherside_walls = reversed(
            new_otherside_walls[1:] + new_otherside_walls[:1]
        )
        segments = zip(
            otherside_walls, 
            new_walls,
            (new_walls[1:] + new_walls[:1])
        )
        for otherside_wall, point_1, point_2 in segments:
            point_1.setup(
                point_2,
                otherside_wall,
                []
            )
            point_2.wall_previous_point = point_1

        otherside_walls = reversed(new_walls[1:] + new_walls[:1])
        segments = zip(
            otherside_walls, 
            new_otherside_walls,
            (new_otherside_walls[1:] + new_otherside_walls[:1])
        )
        for otherside_wall, point_1, point_2 in segments:
            point_1.setup(
                point_2,
                otherside_wall,
                []
            )
            point_2.wall_previous_point = point_1

        for new_wall in new_walls:
            new_wall.reset_panning_and_repeats(None)

        for new_wall in new_otherside_walls:
            new_wall.reset_panning_and_repeats(None)

        new_sector.invalidate_geometry()
        self._sector_to_split.invalidate_geometry()

