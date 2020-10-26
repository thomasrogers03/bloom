# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import core

from . import empty_selector, grid_snapper
from .sector import EditorSector
from .sprite import EditorSprite
from . import move_debug


class Selector(empty_selector.Selector):

    def __init__(self, scene: core.NodePath, sprite: EditorSprite, part: str, snapper: grid_snapper.GridSnapper):
        self._debug = move_debug.MoveDebug(scene)
        self._sprite = sprite
        self._part = part
        self._snapper = snapper
        self._start_position: core.Point3 = None

    def begin_move(self, hit: core.Point3):
        if self._start_position is None:
            self._start_position = self._sprite.position

    def end_move(self):
        self._start_position = None
        self._debug.clear_debug()

    def move(
        self,
        total_delta: core.Vec2,
        delta: core.Vec2,
        total_camera_delta: core.Vec2,
        camera_delta: core.Vec2,
        modified: bool
    ):
        if modified:
            direction_2d = self._snapper.snap_to_angular_grid_2d_scaled(total_camera_delta)
            new_position_2d = core.Point2(self._start_position.x, self._start_position.y) + direction_2d
            new_position_2d = self._snapper.snap_to_grid_2d(new_position_2d)

            new_position = core.Point3(new_position_2d.x, new_position_2d.y, self._start_position.z)
        else:
            new_height = self._snapper.snap_to_grid(self._start_position.z - total_delta.y)
            new_position = core.Point3(self._start_position.x, self._start_position.y, new_height)

        self._debug.update_move_debug(self._start_position, new_position)
        self._sprite.move_to(new_position)

