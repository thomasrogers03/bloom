# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from ... import constants
from .. import map_objects


class AutoLight:

    def __init__(self, all_sectors: map_objects.SectorCollection):
        self._all_sectors = all_sectors

    def apply(self):
        for sector in self._non_sky_sectors():
            distance = self._distance_to_sky_sector(
                sector, 
                constants.REALLY_BIG_NUMBER,
                0,
                set()
            )
            shade = 1 - distance * 0.1
            sector.set_shade(map_objects.EditorSector.FLOOR_PART, shade)
            sector.set_shade(map_objects.EditorSector.CEILING_PART, shade)
            for wall in sector.walls:
                wall.set_shade(None, shade)

    def _distance_to_sky_sector(
        self,
        sector: map_objects.EditorSector,
        distance: int,
        depth: int,
        seen: typing.Set[map_objects.EditorSector]
    ):
        stat = sector.get_stat_for_part(map_objects.EditorSector.CEILING_PART)
        if stat.parallax or depth > 4 or depth >= distance or sector in seen:
            return depth

        for portal in sector.portal_walls():
            new_distance = self._distance_to_sky_sector(
                portal.other_side_sector,
                distance,
                depth + 1,
                seen
            )
            if new_distance < distance:
                distance = new_distance

        if sector.sector_above_ceiling is not None:
            new_distance = self._distance_to_sky_sector(
                sector.sector_above_ceiling,
                distance,
                depth,
                seen
            )
            if new_distance < distance:
                distance = new_distance

        return distance

    def _non_sky_sectors(self):
        for sector in self._all_sectors.sectors:
            stat = sector.get_stat_for_part(map_objects.EditorSector.CEILING_PART)
            if not stat.parallax:
                yield sector
