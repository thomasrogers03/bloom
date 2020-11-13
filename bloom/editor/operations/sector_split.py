# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects
from . import sector_draw, sprite_find_sector, wall_split


class SectorSplit:

    def __init__(
        self, 
        sector_to_split: map_objects.EditorSector,
        all_sectors: map_objects.SectorCollection
    ):
        self._sector_to_split = sector_to_split
        self._all_sectors = all_sectors

    def split(
        self,
        points: typing.List[core.Point2]
    ):
        if len(points) < 2:
            return

        if not sector_draw.is_sector_clockwise(points):
            points = reversed(points)
        points = list(points)
        other_side_points = list(reversed(points))

        first_wall = self._find_wall_for_point(points[0])
        if first_wall is None:
            return

        last_wall = self._find_wall_for_point(points[-1])
        if last_wall is None:
            return

        if not self._can_path_to_wall(first_wall, last_wall):
            return

        wall_split.WallSplit(first_wall).split(points[0])
        wall_split.WallSplit(last_wall).split(points[-1])

        first_wall = first_wall.wall_point_2
        new_sector = self._sector_to_split.new_sector()

        self._sector_to_split.migrate_wall_to_other_sector(first_wall, new_sector)
        next_wall = first_wall.wall_point_2
        while next_wall != last_wall:
            self._sector_to_split.migrate_wall_to_other_sector(next_wall, new_sector)
            next_wall = next_wall.wall_point_2

        if first_wall != last_wall:
            self._sector_to_split.migrate_wall_to_other_sector(last_wall, new_sector)

        new_points = sector_draw.make_wall_points(
            self._wall_base,
            self._sector_to_split,
            points[:-1]
        )
        new_other_side_points = sector_draw.make_wall_points(
            self._wall_base,
            new_sector,
            other_side_points[:-1]
        )
    
        self._join_walls(new_points)
        self._join_walls(new_other_side_points)

        current_sector_first_wall = last_wall.wall_point_2
        current_sector_first_wall.wall_previous_point = new_points[-1]
        new_points[-1].set_wall_point_2(current_sector_first_wall)

        current_sector_last_wall: map_objects.EditorWall = first_wall.wall_previous_point
        current_sector_last_wall.set_wall_point_2(new_points[0])
        new_points[0].wall_previous_point = current_sector_last_wall

        first_wall.wall_previous_point = new_other_side_points[-1]
        new_other_side_points[-1].set_wall_point_2(first_wall)

        last_wall.set_wall_point_2(new_other_side_points[0])
        new_other_side_points[0].wall_previous_point = last_wall

        new_other_side_points = reversed(new_other_side_points)
        for new_wall, new_other_side_wall in zip(new_points, new_other_side_points):
            new_wall.link(new_other_side_wall)

        for sprite in self._sector_to_split.sprites:
            sprite_find_sector.SpriteFindSector(
                sprite,
                self._all_sectors
            ).update_sector()

    @staticmethod
    def _join_walls(walls: typing.List[map_objects.EditorWall]):
        segments = zip(walls, walls[1:])
        for point_1, point_2 in segments:
            point_1.set_wall_point_2(point_2)
            point_2.wall_previous_point = point_1

    @staticmethod
    def _can_path_to_wall(
        start_wall: map_objects.EditorWall, 
        end_wall: map_objects.EditorWall
    ):
        if start_wall == end_wall:
            return True

        next_wall = start_wall.wall_point_2
        while next_wall != start_wall:
            if next_wall == end_wall:
                return True
            next_wall = next_wall.wall_point_2

        return False

    def _find_wall_for_point(self, point: core.Point2):
        for wall in self._sector_to_split.walls:
            if wall.line_segment.point_on_line(point, tolerance=0):
                return wall

        return None

    @property
    def _wall_base(self):
        return self._sector_to_split.walls[0].blood_wall
