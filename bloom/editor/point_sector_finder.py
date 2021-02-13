# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .map_objects.sector import EditorSector
from .map_objects.sprite import EditorSprite


class PointSectorFinder:
    def __init__(
        self,
        point: core.Point2,
        all_sectors: typing.List[EditorSector],
        start_sector: EditorSector,
    ):
        self._point = point
        self._all_sectors = all_sectors
        self._start_sector = start_sector

    def get_new_sector(self):
        current_sector = self._start_sector

        seen: typing.Set[int] = set()
        if current_sector is not None:
            current_sector = self._find_sector_through_portals(
                current_sector, seen, self._point, 10
            )
            if current_sector is not None:
                return current_sector

        for editor_sector in self._all_sectors:
            current_sector = self._find_sector_through_portals(
                editor_sector, seen, self._point, 1000
            )
            if current_sector is not None:
                return current_sector

        return None

    @staticmethod
    def _find_sector_through_portals(
        current_sector: EditorSector,
        seen: typing.Set[EditorSector],
        position: core.Vec2,
        depth_left,
    ):
        if current_sector in seen or depth_left < 1:
            return None

        seen.add(current_sector)
        if current_sector.point_in_sector(position):
            return current_sector

        for adjacent_sector in current_sector.adjacent_sectors():
            found_sector = PointSectorFinder._find_sector_through_portals(
                adjacent_sector, seen, position, depth_left - 1
            )
            if found_sector is not None:
                return found_sector

        return None
