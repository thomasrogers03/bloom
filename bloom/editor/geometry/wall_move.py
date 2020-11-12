# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import grid_snapper
from ..map_objects.wall import EditorWall
from . import empty_move


class WallMove(empty_move.EmptyMove):

    def __init__(self, wall: EditorWall, part: str):
        self._wall = wall
        self._part = part

        self._start_point_1 = self._wall.point_1
        self._start_point_2 = self._wall.point_2

    def get_move_direction(self) -> core.Vec3:
        normal = self._wall.get_normal()
        return core.Vec3(normal.x, normal.y, 0)

    def move(self, move_delta: core.Vec3):
        move_delta_2d = core.Vec2(move_delta.x, move_delta.y)

        new_point_1 = self._start_point_1 + move_delta_2d
        new_point_2 = self._start_point_2 + move_delta_2d

        self._wall.move_point_1_to(new_point_1)
        self._wall.move_point_2_to(new_point_2)
