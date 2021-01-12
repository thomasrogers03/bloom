# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing
from concurrent import futures

import yaml

from ... import constants
from ...tiles import art
from .. import map_objects


class SectorFixer:
    _executor = futures.ThreadPoolExecutor(max_workers=100)

    def __init__(self, all_sectors: map_objects.SectorCollection):
        self._all_sectors = all_sectors

    def apply(self):
        futures = [
            self._executor.submit(self._cleanup_sector, sector)
            for sector in self._all_sectors.sectors
        ]

        cleaned_objects = [
            future.result()
            for future in futures
        ]

        sectors_removed = 0
        walls_removed = 0
        walls_fixed = 0
        sprites_fixed = 0

        for result in cleaned_objects:
            if 'sector' in result:
                sectors_removed += 1
                self._all_sectors.destroy_sector(result['sector'])
            walls_removed += len(result['walls'])
            walls_fixed += result['fixed_wall_count']
            sprites_fixed += result['fixed_sprite_count']

        return sectors_removed, walls_removed, walls_fixed, sprites_fixed

    def _cleanup_sector(self, sector: map_objects.EditorSector):
        result = {}

        if len(sector.walls) < 1:
            result['sector'] = sector
            sector.invalidate_geometry()

        result['walls'], result['fixed_wall_count'] = self._cleanup_walls(sector)
        result['fixed_sprite_count'] = self._cleanup_sprites(sector)
        return result

    def _cleanup_sprites(self, sector: map_objects.EditorSector):
        fix_count = 0

        for sprite in sector.sprites:
            if sprite.get_picnum(None) >= art.ArtManager.MAX_TILES:
                sprite.set_picnum(None, 0)
                fix_count += 1

        return fix_count

    def _cleanup_walls(self, sector: map_objects.EditorSector):
        fix_count = 0
        walls_to_delete: typing.List[map_objects.EditorWall] = []
        for wall in sector.walls:
            while wall.get_length() == 0:
                point_2 = wall.wall_point_2
                wall.set_wall_point_2(point_2.wall_point_2)
                walls_to_delete.append(point_2)

            if wall.wall_previous_point.wall_point_2 != wall:
                wall.wall_previous_point.set_wall_point_2(wall)
                fix_count += 1
            if wall.wall_point_2.wall_previous_point != wall:
                wall.set_wall_point_2(wall.wall_point_2)
                fix_count += 1

            if wall.get_picnum(None) >= art.ArtManager.MAX_TILES:
                wall.set_picnum(None, 0)
                fix_count += 1

            if wall.other_side_wall is not None:
                if wall.other_side_wall.other_side_wall is None or \
                        wall.other_side_wall.point_2 != wall.point_1:
                    fix_count += 1
                    wall.unlink()

        for wall in walls_to_delete:
            if wall.other_side_wall is not None:
                wall.other_side_wall.unlink()
            sector.remove_wall(wall)

        if len(walls_to_delete) > 0 or fix_count > 0:
            sector.invalidate_geometry()

        return walls_to_delete, fix_count
