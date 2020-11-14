# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from ..map_objects import sector, wall
from . import wall_split


class SectorWallLink:

    def __init__(
        self, 
        wall_to_link: wall.EditorWall, 
        all_sectors: sector.SectorCollection
    ):
        self._wall_to_link = wall_to_link
        self._link_wall_sector: sector.EditorSector = self._wall_to_link.sector
        self._all_sectors = all_sectors

    def try_link_wall(self):
        if self._wall_to_link.other_side_sector is not None:
            return

        seen_sectors: typing.Set[sector.EditorSector] = set()
        if self._do_try_link_wall(self._link_wall_sector, seen_sectors):
            return

        for editor_sector in self._all_sectors.sectors:
            if self._do_try_link_wall(editor_sector, seen_sectors, include_self=True):
                return

    @staticmethod
    def _try_link(test_wall: wall.EditorWall, wall_to_link: wall.EditorWall):
        if wall_to_link == test_wall or \
            wall_to_link == test_wall.wall_previous_point or \
                wall_to_link == test_wall.wall_point_2:
            return False

        overlap = test_wall.line_segment.segment_within(wall_to_link.line_segment)
        if overlap and not overlap.is_empty:
            test_wall.invalidate_geometry()
            wall_to_link.invalidate_geometry()

            if test_wall.point_2 == overlap.point_1:
                if test_wall.point_1 != overlap.point_2:
                    wall_split.WallSplit(test_wall).split(overlap.point_2)
                    test_wall = test_wall.wall_point_2
            else:
                wall_split.WallSplit(test_wall).split(overlap.point_1)
                if test_wall.point_1 != overlap.point_2:
                    wall_split.WallSplit(test_wall).split(overlap.point_2)
                    test_wall = test_wall.wall_point_2
            test_wall._other_side_wall
            test_wall.link(wall_to_link)
            return True

        overlap = wall_to_link.line_segment.segment_within(test_wall.line_segment)
        if overlap and not overlap.is_empty:
            test_wall.invalidate_geometry()
            wall_to_link.invalidate_geometry()

            wall_split.WallSplit(wall_to_link).split(test_wall.point_1)
            wall_split.WallSplit(wall_to_link).split(test_wall.point_2)
            test_wall.link(wall_to_link)
            wall_to_link.wall_point_2.link(test_wall)
            return True

        return False

    def _do_try_link_wall(
        self,
        test_sector: sector.EditorSector,
        seen_sectors: typing.Set[sector.EditorSector],
        depth_left=100,
        include_self=False
    ):
        if depth_left < 1 or test_sector in seen_sectors:
            return False

        seen_sectors.add(test_sector)

        if include_self:
            for editor_wall in test_sector.walls:
                if editor_wall.other_side_sector is None:
                    if self._try_link(editor_wall, self._wall_to_link):
                        test_sector.validate()
                        return True

        for portal in test_sector.portal_walls():
            result = self._do_try_link_wall(
                portal.other_side_sector,
                seen_sectors,
                depth_left=depth_left - 1,
                include_self=True
            )
            if result:
                return True

        return False
