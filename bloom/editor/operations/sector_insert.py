# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from ... import map_data
from .. import map_objects
from ..map_objects.drawing import sector as drawing_sector
from . import sector_draw, sprite_find_sector


class SectorInsert:
    def __init__(
        self,
        sector_to_split: map_objects.EditorSector,
        all_sectors: map_objects.SectorCollection,
    ):
        self._sector_to_split = sector_to_split
        self._all_sectors = all_sectors

    def insert(self, points: typing.List[core.Point2]):
        if len(points) < 3:
            return

        with self._all_sectors.undos.multi_step_undo("Sector Insert"):
            new_sector = self._do_insert(points)

            sector_above = self._sector_to_split.sector_above_ceiling
            previous_sector = new_sector
            while sector_above is not None:
                offset = sector_above.get_above_draw_offset()
                offset_points = [point + offset.xy for point in points]
                above_new_sector = SectorInsert(sector_above, self._all_sectors)._do_insert(offset_points)
                above_new_sector.link(sector_above.ror_type, previous_sector)

                previous_sector = above_new_sector
                sector_above = sector_above.sector_above_ceiling

            previous_sector = new_sector
            sector_below = self._sector_to_split.sector_below_floor
            while sector_below is not None:
                offset = sector_below.get_below_draw_offset()
                offset_points = [point + offset.xy for point in points]
                below_new_sector = SectorInsert(sector_below, self._all_sectors)._do_insert(offset_points)
                ror_type = sector_below.sector_above_ceiling.ror_type
                previous_sector.link(ror_type, below_new_sector)

                previous_sector = below_new_sector
                sector_below = sector_below.sector_below_floor

    def _do_insert(self, points: typing.List[core.Point2]):
        if self._sector_to_split is None:
            new_sector = self._all_sectors.create_empty_sector()
        else:
            new_sector = self._all_sectors.create_sector(self._sector_to_split)

        if not drawing_sector.Sector.are_points_clockwise(points):
            points = list(reversed(points))

        if self._sector_to_split is not None:
            new_points = sector_draw.make_wall_points(
                self._wall_base, self._sector_to_split, points
            )
        new_otherside_points = sector_draw.make_wall_points(
            self._wall_base, new_sector, points
        )

        if self._sector_to_split is not None:
            otherside_walls = new_otherside_points[1:] + new_otherside_points[:1]
            for editor_wall, otherside_wall in zip(new_points, otherside_walls):
                editor_wall.link(otherside_wall)

        if self._sector_to_split is not None:
            self._join_walls(new_points)
        self._join_walls(reversed(new_otherside_points))

        if self._sector_to_split is not None:
            for new_wall in new_points:
                new_wall.reset_panning_and_repeats(None)

        for new_wall in new_otherside_points:
            new_wall.reset_panning_and_repeats(None)

        if self._sector_to_split is not None:
            self._sector_to_split.invalidate_geometry()
        new_sector.invalidate_geometry()

        if self._sector_to_split is not None:
            for sprite in self._sector_to_split.sprites:
                sprite_find_sector.SpriteFindSector(
                    sprite, self._all_sectors.sectors
                ).update_sector()

        return new_sector

    @staticmethod
    def _join_walls(walls: typing.Iterable[map_objects.EditorWall]):
        walls = list(walls)
        segments = zip(walls, walls[1:] + walls[:1])
        for point_1, point_2 in segments:
            point_1.set_wall_point_2(point_2)
            point_2.wall_previous_point = point_1

    @property
    def _wall_base(self):
        if self._sector_to_split is None:
            return map_data.wall.Wall()
        return self._sector_to_split.walls[0].blood_wall
