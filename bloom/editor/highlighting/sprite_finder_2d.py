# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from ... import constants
from .. import map_objects


class SpriteFinder2D:
    def __init__(self, position: core.Point2):
        self._position = position

    def closest_sprite(self, sprites: typing.List[map_objects.EditorSprite]):
        closest_distance = constants.REALLY_BIG_NUMBER
        closest_sprite: map_objects.EditorSprite = None

        for sprite in sprites:
            distance_to_sprite = (self._position - sprite.origin_2d).length()
            if distance_to_sprite is None or distance_to_sprite > sprite.size.x:
                continue

            if distance_to_sprite < closest_distance:
                closest_distance = distance_to_sprite
                closest_sprite = sprite

        return closest_sprite, closest_distance
