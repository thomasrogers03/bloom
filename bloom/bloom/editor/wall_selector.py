# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import edit_mode
from . import empty_selector, grid_snapper, move_debug
from .sector import EditorSector
from .wall import EditorWall


class Selector(empty_selector.Selector):
    _NO_POINT = -1
    _POINT_1 = 0
    _POINT_2 = 1

    def __init__(self, scene: core.NodePath, wall: EditorWall, part: str, snapper: grid_snapper.GridSnapper):
        self._debug = move_debug.MoveDebug(scene)
        self._wall = wall
        self._part = part
        self._snapper = snapper
        self._hit: core.Point3 = None
        self._hit_near_wall_point = self._NO_POINT
        self._start_point_1: core.Point2 = None
        self._start_point_2: core.Point2 = None

    def get_selected(self):
        return self._wall

    def get_picnum(self):
        return self._wall.get_picnum(self._part)

    def set_picnum(self, picnum: int):
        self._wall.set_picnum(self._part, picnum)

    def begin_move(self, hit: core.Point3):
        if self._hit is None:
            self._hit = hit
            self._start_point_1 = self._wall.point_1
            self._start_point_2 = self._wall.point_2
            self._hit_near_wall_point = self._is_hit_near_wall_point()

    def end_move(self):
        self._hit = None
        self._start_point_1 = None
        self._start_point_2 = None
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
            move_direction = total_camera_delta.normalized()
        elif self._hit_near_wall_point == self._NO_POINT:
            move_direction = self._wall.get_normal()
        else:
            move_direction = self._wall.get_normalized_direction()
        amount = move_direction.dot(total_camera_delta)
        move_direction = move_direction * amount


        if self._hit_near_wall_point == self._NO_POINT:
            move_direction = self._snapper.snap_to_grid_2d(move_direction)
            new_point_1 = self._start_point_1 + move_direction
            new_point_2 = self._start_point_2 + move_direction
        
            self._debug.update_move_debug_2d_offset(core.Vec2(self._hit.x, self._hit.y), move_direction, self._hit.z)

            self._wall.move_point_1_to(new_point_1)
            self._wall.move_point_2_to(new_point_2)
        elif self._hit_near_wall_point == self._POINT_1:
            move_direction = self._snapper.snap_to_angular_grid_2d_scaled(move_direction)
            new_point_1 = self._snapper.snap_to_grid_2d(self._start_point_1 + move_direction)
            
            self._debug.update_move_debug_2d(self._start_point_1, new_point_1, self._hit.z)
            self._wall.move_point_1_to(new_point_1)
        else:
            move_direction = self._snapper.snap_to_angular_grid_2d_scaled(move_direction)
            new_point_2 = self._snapper.snap_to_grid_2d(self._start_point_2 + move_direction)
            
            self._debug.update_move_debug_2d(self._start_point_2, new_point_2, self._hit.z)
            self._wall.move_point_2_to(new_point_2)

    def split(self, hit: core.Point3, sectors: typing.List[EditorSector], modified: bool):
        if modified:
            self._wall.extrude(sectors)
        else:
            split_position = self._snapper.snap_to_grid_2d(core.Point2(hit.x, hit.y))
            self._wall.split(split_position)

    def _is_hit_near_wall_point(self):
        hit_2d = core.Point2(self._hit.x, self._hit.y)
        threshold = 512
        threshold_squared = threshold * threshold
        if (hit_2d - self._wall.point_1).length_squared() < threshold_squared:
            return self._POINT_1

        if (hit_2d - self._wall.point_2).length_squared() < threshold_squared:
            return self._POINT_2

        return self._NO_POINT
