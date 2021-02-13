# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing
from concurrent import futures

import yaml

from ... import constants, find_resource
from .. import map_objects


def _load_light_types():
    path = find_resource("light_tiles.yaml")
    with open(path, "r") as file:
        result = yaml.safe_load(file.read())
    return {key: set(value) for key, value in result.items()}


class AutoLight:
    _light_types = _load_light_types()
    _executor = futures.ThreadPoolExecutor(max_workers=100)

    def __init__(self, all_sectors: map_objects.SectorCollection):
        self._all_sectors = all_sectors
        self._sectors_having_light: typing.Set[map_objects.EditorSector] = set()

    def apply(self):
        futures = []
        for sector in self._all_sectors.sectors:
            if self._sector_has_light(sector):
                self._sectors_having_light.add(sector)

        for sector in self._all_sectors.sectors:
            future = self._executor.submit(self._apply_shade, sector)
            futures.append(future)

        for future in futures:
            future.result()

    def _apply_shade(self, sector: map_objects.EditorSector):
        distance = self._distance_to_sky_sector(
            sector, constants.REALLY_BIG_NUMBER, 0, set()
        )
        shade = 1 - distance * 0.05
        sector.set_shade(map_objects.EditorSector.FLOOR_PART, shade)
        sector.set_shade(map_objects.EditorSector.CEILING_PART, shade)
        for wall in sector.walls:
            wall.set_shade(None, shade)

    def _distance_to_sky_sector(
        self,
        sector: map_objects.EditorSector,
        distance: int,
        depth: int,
        seen: typing.Set[map_objects.EditorSector],
    ):
        if sector in seen:
            return constants.REALLY_BIG_NUMBER

        if depth > 6 or depth >= distance or sector in self._sectors_having_light:
            return depth

        new_seen = seen | {
            sector,
        }
        for portal in sector.portal_walls():
            new_distance = self._distance_to_sky_sector(
                portal.other_side_sector, distance, depth + 1, new_seen
            )
            if new_distance < distance:
                distance = new_distance

        if sector.sector_above_ceiling is not None:
            new_distance = self._distance_to_sky_sector(
                sector.sector_above_ceiling, distance, depth, new_seen
            )
            if new_distance < distance:
                distance = new_distance

        return distance

    def _sector_has_light(self, sector: map_objects.EditorSector):
        stat = sector.get_stat_for_part(map_objects.EditorSector.CEILING_PART)
        return (
            stat.parallax
            or sector.get_picnum(map_objects.EditorSector.FLOOR_PART)
            in self._light_types["floors"]
            or sector.get_picnum(map_objects.EditorSector.CEILING_PART)
            in self._light_types["ceilings"]
            or self._sector_has_light_sprite(sector)
        )

    def _sector_has_light_sprite(self, sector: map_objects.EditorSector):
        for sprite in sector.sprites:
            if sprite.get_picnum(None) in self._light_types["sprites"]:
                return True
        return False
