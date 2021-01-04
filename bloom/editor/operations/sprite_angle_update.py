# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from ... import editor
from .. import map_objects


class SpriteAngleUpdate:

    def __init__(self, sprite: map_objects.EditorSprite):
        self._sprite = sprite

    def increment(self, amount):
        with self._sprite.change_blood_object():
            new_value = self._sprite.theta + amount
            self._sprite.set_theta(new_value)
