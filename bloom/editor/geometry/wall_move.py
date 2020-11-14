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

    def move(self, move_delta: core.Vec3, snapper: grid_snapper.GridSnapper):
        move_delta_2d = snapper.snap_to_grid_2d(move_delta.xy)

        new_point_1 = self._start_point_1 + move_delta_2d
        new_point_2 = self._start_point_2 + move_delta_2d

        walls_at_point_1 = self._wall.all_walls_at_point_1()
        walls_at_point_2 = self._wall.wall_point_2.all_walls_at_point_1()

        for wall in walls_at_point_1:
            wall.teleport_point_1_to(new_point_1)
        
        for wall in walls_at_point_2:
            wall.teleport_point_1_to(new_point_2)
