# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import grid_snapper, map_objects
from . import empty_move


class SectorMoveWalls(empty_move.EmptyMove):

    def __init__(self, sector: map_objects.EditorSector):
        self._sector = sector
        self._wall_start_points = [wall.point_1 for wall in self._sector.walls]
        self._sprite_start_points = [sprite.origin for sprite in self._sector.sprites]

    def get_move_direction(self):
        return core.Vec3(0, 0, 0)

    def move(self, move_delta: core.Vec3, snapper: grid_snapper.GridSnapper):
        move_delta_2d = snapper.snap_to_grid_2d(move_delta.xy)
        for wall, start_point in zip(self._sector.walls, self._wall_start_points):
            new_position = start_point + move_delta_2d
            for sub_wall in wall.all_walls_at_point_1():
                sub_wall.teleport_point_1_to(new_position)

        for sprite, start_point in zip(self._sector.sprites, self._sprite_start_points):
            new_position = core.Point3(
                start_point.x + move_delta_2d.x,
                start_point.y + move_delta_2d.y,
                start_point.z
            )
            sprite.move_to(new_position)
