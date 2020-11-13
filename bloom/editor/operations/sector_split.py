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

        self._migrate_new_walls(new_sector, points[0], points[-1])

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

        self._join_new_walls_to_current_sector(
            new_sector,
            new_points[0],
            new_points[-1],
            points[-1]
        )

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

    def _migrate_new_walls(
        self, 
        new_sector: map_objects.EditorSector, 
        first_point: core.Point2, 
        last_point: core.Point2
    ):
        current_wall = self._find_split_sector_wall_on_point(first_point)
        stop_wall = self._find_split_sector_wall_on_point(last_point)

        while current_wall != stop_wall:
            self._sector_to_split.migrate_wall_to_other_sector(current_wall, new_sector)
            current_wall = current_wall.wall_point_2

    def _join_new_walls_to_current_sector(
        self, 
        new_sector: map_objects.EditorSector,
        first_new_wall: map_objects.EditorWall,
        last_new_wall: map_objects.EditorWall,
        last_point: core.Point2
    ):
        old_point_2 = self._find_wall_on_point(new_sector, first_new_wall.point_1)
        first_wall: map_objects.EditorWall = old_point_2.wall_previous_point
        first_wall.set_wall_point_2(first_new_wall)

        last_wall = self._find_split_sector_wall_on_point(last_point)
        last_new_wall.set_wall_point_2(last_wall)

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

    def _find_split_sector_wall_on_point(self, point: core.Point2):
        return self._find_wall_on_point(self._sector_to_split, point)

    def _find_wall_for_point(self, point: core.Point2):
        for wall in self._sector_to_split.walls:
            if wall.line_segment.point_on_line(point, tolerance=0):
                return wall

        return None

    @staticmethod
    def _find_wall_on_point(sector: map_objects.EditorSector, point: core.Point2):
        for wall in sector.walls:
            if wall.point_1 == point:
                return wall

        return None

    @property
    def _wall_base(self):
        return self._sector_to_split.walls[0].blood_wall
