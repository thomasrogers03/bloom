# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from .. import grid_snapper


class EmptyMove:
    def get_move_direction(self) -> core.Vec3:
        raise NotImplementedError

    def move(self, move_delta: core.Vec3, snapper: grid_snapper.GridSnapper):
        raise NotImplementedError
