# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects

class SpriteFlip:

    def __init__(self, sprite: map_objects.EditorSprite):
        self._sprite = sprite

    def flip(self):
        self._sprite.invalidate_geometry()
        
        stat = self._sprite.sprite.sprite.stat
        if stat.xflip and stat.yflip:
            stat.xflip = 0
        elif stat.xflip:
            stat.xflip = 1
            stat.yflip = 1
        elif stat.yflip:
            stat.yflip = 0
        else:
            stat.xflip = 1