# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects


class SpriteFindSector:

    def __init__(
        self, 
        sprite: map_objects.EditorSprite, 
        all_sectors: map_objects.SectorCollection
    ):
        self._sprite = sprite
        self._all_sectors = all_sectors

    def update_sector(self):
        new_sector = self._get_new_sector()
        old_sector = self._sprite.get_sector()
        old_sector.migrate_sprite_to_other_sector(self._sprite, new_sector)

    def _get_new_sector(self):
        current_sector = self._sprite.get_sector()
        position = self._sprite.origin
        
        seen: typing.Set[int] = set()
        if current_sector is not None:
            current_sector = self._find_sector_through_portals(
                current_sector,
                seen,
                position,
                10
            )
            if current_sector is not None:
                return current_sector

        for editor_sector in self._all_sectors.sectors:
            current_sector = self._find_sector_through_portals(
                editor_sector,
                seen,
                position,
                1000
            )
            if current_sector is not None:
                return current_sector

        return None

    def _find_sector_through_portals(
        self,
        current_sector: map_objects.EditorSector,
        seen: typing.Set[map_objects.EditorSector],
        position: core.Vec3,
        depth_left
    ):
        if current_sector in seen or depth_left < 1:
            return None

        seen.add(current_sector)
        if current_sector.vector_in_sector(position):
            return current_sector

        for adjacent_sector in current_sector.adjacent_sectors():
            found_sector = self._find_sector_through_portals(
                adjacent_sector,
                seen,
                position,
                depth_left - 1
            )
            if found_sector is not None:
                return found_sector

        return None
