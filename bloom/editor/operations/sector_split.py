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

        if winding < 1:
            points = reversed(points)
        points = list(points)

        new_points = self._make_wall_points(self._sector_to_split, points)
        new_otherside_points = self._make_wall_points(new_sector, points)

        otherside_walls = new_otherside_points[1:] + new_otherside_points[:1]
        for editor_wall, otherside_wall in zip(new_points, otherside_walls):
            editor_wall.link(otherside_wall)
            otherside_wall.link(editor_wall)

        self._join_walls(new_points)
        self._join_walls(reversed(new_otherside_points))

        for new_wall in new_points:
            new_wall.reset_panning_and_repeats(None)

        for new_wall in new_otherside_points:
            new_wall.reset_panning_and_repeats(None)

        new_sector.invalidate_geometry()
        self._sector_to_split.invalidate_geometry()

    def _join_walls(self, walls: typing.List[map_objects.EditorWall]):
        walls = list(walls)
        segments = zip(walls, walls[1:] + walls[:1])
        for point_1, point_2 in segments:
            point_1.set_wall_point_2(point_2)
            point_2.wall_previous_point = point_1

    def _make_wall_points(
        self, 
        editor_sector: map_objects.EditorSector, 
        points: typing.List[core.Vec2]
    ) -> typing.List[map_objects.EditorWall]:
        result: typing.List[map_objects.EditorWall] = []
        for point in points:
            new_blood_wall = self._wall_base.copy()
            new_blood_wall.wall.position_x = int(point.x)
            new_blood_wall.wall.position_y = int(point.y)

            new_wall = editor_sector.add_wall(new_blood_wall)
            result.append(new_wall)
        return result

    @property
    def _wall_base(self):
        return self._sector_to_split.walls[0].blood_wall