# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import grid_snapper, map_objects
from . import empty_move


class SectorMoveWalls(empty_move.EmptyMove):

    def __init__(self, sector: map_objects.EditorSector):
        self._sector = sector
        self._start_points = [wall.point_1 for wall in self._sector.walls]

    def get_move_direction(self):
        return core.Vec3(0, 0, 0)

    def move(self, move_delta: core.Vec3, snapper: grid_snapper.GridSnapper):
        move_delta_2d = snapper.snap_to_grid_2d(move_delta.xy)
        for wall, start_point in zip(self._sector.walls, self._start_points):
            new_position = start_point + move_delta_2d
            wall.teleport_point_1_to(new_position)
