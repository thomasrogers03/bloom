# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0


from panda3d import core

from .. import grid_snapper, map_objects
from . import empty_move, wall_repeat_adjust


class WallMove(empty_move.EmptyMove):
    def __init__(self, wall: map_objects.EditorWall, part: str):
        self._wall = wall
        self._part = part

        self._start_point_1 = self._wall.point_1
        self._start_point_2 = self._wall.point_2

    @property
    def _is_vertex(self):
        return "_vertex_" in self._part

    def get_move_direction(self) -> core.Vec3:
        if self._is_vertex:
            direction = self._wall.get_normalized_direction()
            return core.Vec3(direction.x, direction.y, 0)

        normal = self._wall.get_normal()
        return core.Vec3(normal.x, normal.y, 0)

    def move(self, move_delta: core.Vec3, snapper: grid_snapper.GridSnapper):
        if self._is_vertex:
            new_point_1 = snapper.snap_to_grid_2d(self._start_point_1 + move_delta.xy)
        else:
            move_delta_2d = snapper.snap_to_grid_2d(move_delta.xy)
            new_point_1 = self._start_point_1 + move_delta_2d

        self._move_vertex(self._wall, new_point_1)
        if not self._is_vertex:
            new_point_2 = self._start_point_2 + move_delta_2d
            self._move_vertex(self._wall.wall_point_2, new_point_2)

    @staticmethod
    def _move_vertex(wall: map_objects.EditorWall, new_position: core.Point2):
        walls_to_move = wall.all_walls_at_point_1()
        for point in walls_to_move:
            repeat_adjust_previous_point = wall_repeat_adjust.WallRepeatAdjust(
                point.wall_previous_point
            )
            repeat_adjust = wall_repeat_adjust.WallRepeatAdjust(point)

            point.teleport_point_1_to(new_position)

            repeat_adjust_previous_point.adjust()
            repeat_adjust.adjust()
