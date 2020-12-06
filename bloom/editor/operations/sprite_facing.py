# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects

class SpriteFacing:

    def __init__(self, sprite: map_objects.EditorSprite):
        self._sprite = sprite

    def change_facing(self):
        self._sprite.invalidate_geometry()
        
        stat = self._sprite.sprite.sprite.stat
        stat.facing = (stat.facing + 1) % 3