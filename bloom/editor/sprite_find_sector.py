# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from . import point_sector_finder
from .map_objects.sector import EditorSector
from .map_objects.sprite import EditorSprite


class SpriteFindSector:

    def __init__(
        self, 
        sprite: EditorSprite, 
        all_sectors: typing.List[EditorSector]
    ):
        self._sprite = sprite
        self._all_sectors = all_sectors

    def update_sector(self):
        finder = point_sector_finder.PointSectorFinder(
            self._sprite.origin_2d, 
            self._all_sectors, 
            self._sprite.get_sector()
        )

        new_sector = finder.get_new_sector()
        old_sector = self._sprite.get_sector()
        if new_sector is not None:
            old_sector.migrate_sprite_to_other_sector(self._sprite, new_sector)

