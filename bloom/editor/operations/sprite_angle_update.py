# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from ... import editor
from .. import map_objects


class SpriteAngleUpdate:

    def __init__(self, sprite: map_objects.EditorSprite):
        self._sprite = sprite

    def increment(self, amount):
        self._sprite.invalidate_geometry()
        new_value = self._sprite.theta + amount
        self._sprite.sprite.sprite.theta = editor.to_build_angle(new_value)