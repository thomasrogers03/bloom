# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0


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

    def move(self, move_delta: core.Vec3, snapper: grid_snapper.GridSnapper):

        new_position = self._start_position + move_delta
        if move_delta.z != 0:
            new_position.z = snapper.snap_to_grid(new_position.z)
        else:
            new_position.xy = snapper.snap_to_grid_2d(new_position.xy)
        self._sprite.move_to(new_position)
