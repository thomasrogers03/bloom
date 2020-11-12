# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import grid_snapper
from ..map_objects.sprite import EditorSprite
from . import empty_move


class SpriteMove(empty_move.EmptyMove):

    def __init__(self, sprite: EditorSprite):
        self._sprite = sprite
        self._start_position = self._sprite.origin

    def get_move_direction(self) -> core.Vec3:
        return core.Vec3(0, 0, -1)

    def move(self, move_delta: core.Vec3):
        new_position = self._start_position + move_delta
        self._sprite.move_to(new_position)
