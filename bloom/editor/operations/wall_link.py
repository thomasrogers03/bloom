# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from .. import map_objects
from . import wall_split


class SectorWallLink:

    def __init__(
        self,
        wall_to_link: map_objects.EditorWall,
        all_sectors: map_objects.SectorCollection
    ):
        self._wall_to_link = wall_to_link
        self._link_wall_sector: map_objects.EditorSector = self._wall_to_link.sector
        self._all_sectors = all_sectors

    def try_link_wall(self):
        with self._wall_to_link.undos.multi_step_undo('Wall Link'):
            if self._try_link_single_wall():
                if self._wall_to_link.other_side_wall is None:
                    self.try_link_wall()
                elif self._wall_to_link.wall_point_2.other_side_wall is None:
                    SectorWallLink(
                        self._wall_to_link.wall_point_2,
                        self._all_sectors
                    ).try_link_wall()

    def _try_link_single_wall(self):
        if self._wall_to_link.other_side_sector is not None:
            return False

        seen_sectors: typing.Set[map_objects.EditorSector] = set()
        if self._do_try_link_wall(self._link_wall_sector, seen_sectors):
            return True

        for editor_sector in self._all_sectors.sectors:
            if self._do_try_link_wall(editor_sector, seen_sectors, include_self=True):
                return True
        return False

    @staticmethod
    def _try_link(test_wall: map_objects.EditorWall, wall_to_link: map_objects.EditorWall):
        if SectorWallLink._cannot_link(test_wall, wall_to_link):
            return False

        overlap = test_wall.line_segment.segment_within(wall_to_link.line_segment)
        if overlap and not overlap.is_empty:
            test_wall.invalidate_geometry()
            wall_to_link.invalidate_geometry()

            if test_wall.point_2 == overlap.point_1:
                if test_wall.point_1 != overlap.point_2:
                    wall_split.WallSplit(test_wall, overlap.point_2).split()
                    test_wall = test_wall.wall_point_2
                    if SectorWallLink._cannot_link(test_wall, wall_to_link):
                        return False
            else:
                wall_split.WallSplit(test_wall, overlap.point_1).split()
                if test_wall.point_1 != overlap.point_2:
                    wall_split.WallSplit(test_wall, overlap.point_2).split()
                    test_wall = test_wall.wall_point_2
                    if SectorWallLink._cannot_link(test_wall, wall_to_link):
                        return False
            test_wall.link(wall_to_link)
            return True

        overlap = wall_to_link.line_segment.segment_within(test_wall.line_segment)
        if overlap and not overlap.is_empty:
            SectorWallLink._try_link(wall_to_link, test_wall)
            return True

        return False

    @staticmethod
    def _cannot_link(test_wall: map_objects.EditorWall, wall_to_link: map_objects.EditorWall):
        return wall_to_link == test_wall or \
            wall_to_link == test_wall.wall_previous_point or \
            wall_to_link == test_wall.wall_point_2 or \
            test_wall.other_side_wall is not None

    def _do_try_link_wall(
        self,
        test_sector: map_objects.EditorSector,
        seen_sectors: typing.Set[map_objects.EditorSector],
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
