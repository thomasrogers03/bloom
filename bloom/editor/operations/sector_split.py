# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects
from ..map_objects.drawing import sector as drawing_sector
from . import sector_draw, sprite_find_sector, wall_split


class SectorSplit:

    def __init__(
        self, 
        sector_to_split: map_objects.EditorSector,
        all_sectors: map_objects.SectorCollection
    ):
        self._sector_to_split = sector_to_split
        self._all_sectors = all_sectors
        self._allocated_walls: typing.Set[map_objects.EditorWall] = set()

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

        if first_wall == last_wall:
            first_point_portion = first_wall.line_segment.get_point_portion_of_line(points[0])
            last_point_portion = first_wall.line_segment.get_point_portion_of_line(points[-1])
            if last_point_portion > first_point_portion:
                wall_split.WallSplit(first_wall).split(points[-1])
                wall_split.WallSplit(first_wall).split(points[0])
            else:
                wall_split.WallSplit(first_wall).split(points[0])
                wall_split.WallSplit(first_wall).split(points[-1])
        else:
            wall_split.WallSplit(first_wall).split(points[0])
            wall_split.WallSplit(last_wall).split(points[-1])

        new_sector = self._all_sectors.create_sector(self._sector_to_split)
        self._migrate_new_walls(new_sector, points[0], points[-1])

        new_points = sector_draw.make_wall_points(
            self._wall_base,
            self._sector_to_split,
            points[:-1]
        )
        self._allocated_walls |= set(new_points)

        new_other_side_points = sector_draw.make_wall_points(
            self._wall_base,
            new_sector,
            other_side_points[:-1]
        )
        self._allocated_walls |= set(new_other_side_points)
    
        self._join_walls(new_points)
        self._join_walls(new_other_side_points)

        previous_wall_current_sector, next_wall_current_sector = self._get_walls_to_join_points_to_current_sector(
            new_sector,
            new_points[0],
            new_points[-1],
            points[-1]
        )

        previous_wall_new_sector, next_wall_new_sector = self._get_walls_to_join_points_to_new_sector(
            new_sector,
            new_other_side_points[0],
            new_other_side_points[-1],
            points[0]
        )

        previous_wall_current_sector.set_wall_point_2(new_points[0])
        new_points[-1].set_wall_point_2(next_wall_current_sector)

        previous_wall_new_sector.set_wall_point_2(new_other_side_points[0])
        new_other_side_points[-1].set_wall_point_2(next_wall_new_sector)

        if drawing_sector.Sector.is_sector_section_clockwise(new_other_side_points[0]):
            outer_bunch: map_objects.EditorWall = None
            seen_walls: typing.Set[map_objects.EditorWall] = set(self._allocated_walls)
            for wall in self._sector_to_split.walls:
                if wall in seen_walls:
                    continue

                if not drawing_sector.Sector.is_sector_section_clockwise(wall):
                    outer_bunch = wall
                    break

                for sub_wall in wall.iterate_wall_bunch():
                    seen_walls.add(sub_wall)

            for wall in outer_bunch.iterate_wall_bunch():
                self._sector_to_split.migrate_wall_to_other_sector(wall, new_sector)
        else:
            walls_to_migrate = []
            for wall in self._sector_to_split.walls:
                if wall in self._allocated_walls:
                    continue

                if new_sector.point_in_sector(wall.point_2):
                    for sub_wall in wall.iterate_wall_bunch():
                        self._allocated_walls.add(sub_wall)
                        walls_to_migrate.append(sub_wall)

            for wall in walls_to_migrate:
                self._sector_to_split.migrate_wall_to_other_sector(wall, new_sector)

        new_other_side_points = list(reversed(new_other_side_points))
        for new_wall, new_other_side_wall in zip(new_points, new_other_side_points):
            new_wall.link(new_other_side_wall)

        for new_wall in new_points + new_other_side_points:
            new_wall.reset_panning_and_repeats(None)

        for sprite in self._sector_to_split.sprites:
            sprite_find_sector.SpriteFindSector(
                sprite,
                self._all_sectors.sectors
            ).update_sector()

    def _migrate_new_walls(
        self, 
        new_sector: map_objects.EditorSector, 
        first_point: core.Point2, 
        last_point: core.Point2
    ):
        start_wall = self._find_split_sector_wall_on_point(first_point)
        stop_wall = self._find_split_sector_wall_on_point(last_point)

        current_wall = start_wall
        while current_wall != stop_wall:
            self._allocated_walls.add(current_wall)
            self._sector_to_split.migrate_wall_to_other_sector(current_wall, new_sector)
            current_wall = current_wall.wall_point_2

        while current_wall != start_wall:
            self._allocated_walls.add(current_wall)
            current_wall = current_wall.wall_point_2

    def _get_walls_to_join_points_to_current_sector(
        self, 
        new_sector: map_objects.EditorSector,
        first_new_wall: map_objects.EditorWall,
        last_new_wall: map_objects.EditorWall,
        last_point: core.Point2
    ):
        old_point_2 = sector_draw.find_wall_on_point(new_sector, first_new_wall.point_1)
        first_wall: map_objects.EditorWall = old_point_2.wall_previous_point
        last_wall = self._find_split_sector_wall_on_point(last_point)

        return first_wall, last_wall

    def _get_walls_to_join_points_to_new_sector(
        self, 
        new_sector: map_objects.EditorSector,
        first_new_wall: map_objects.EditorWall,
        last_new_wall: map_objects.EditorWall,
        last_point: core.Point2
    ):
        old_point_2 = self._find_split_sector_wall_on_point(first_new_wall.point_1)
        first_wall: map_objects.EditorWall = old_point_2.wall_previous_point
        last_wall = sector_draw.find_wall_on_point(new_sector, last_point)

        return first_wall, last_wall

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
        return sector_draw.find_wall_on_point(self._sector_to_split, point)

    def _find_wall_for_point(self, point: core.Point2):
        for wall in self._sector_to_split.walls:
            if wall.line_segment.point_on_line(point, tolerance=0):
                return wall

        return None

    @property
    def _wall_base(self):
        return self._sector_to_split.walls[0].blood_wall
