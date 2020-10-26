# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .sector import EditorSector
from .wall import EditorWall


class WallBunch:

    def __init__(
        self,
        start_wall: EditorWall,
        project_callback: typing.Callable[[core.Point2], core.Point3]
    ):
        self._start_wall = start_wall
        self._other_side_sector = self._start_wall.other_side_sector
        self._project_callback = project_callback

        point = self._project_callback(self._start_wall.point_1)
        self._min_x = point.x
        self._max_x = point.x
        self._max_z = point.z
        self._min_z = point.z

    def add_wall_previous(self, wall: EditorWall) -> bool:
        if not self._check_sameness(wall, wall.other_side_sector):
            return False

        point = self._project_callback(wall.point_1)
        if not self._check_depth(point):
            return False

        if point.x > self._min_x:
            return False

        self._min_x = point.x
        return True

    def add_wall_next(self, wall: EditorWall) -> bool:
        if not self._check_sameness(wall, wall.wall_previous_point.other_side_sector):
            return False

        point = self._project_callback(wall.point_1)
        if not self._check_depth(point):
            return False

        if point.x < self._max_x:
            return False

        self._max_x = point.x
        return True

    def make_portal(self, min_x, max_x, max_z):
        if self._min_x > max_x or self._max_x < min_x or self._min_z > max_z:
            return None, None
        return core.Point3(
            max(self._min_x, min_x),
            min(self._max_x, max_x),
            min(self._max_z, max_z)
        ), self._other_side_sector

    def __str__(self, *args, **kwargs):
        return f'portal_sector: {self._other_side_sector}, min_x: {self._min_x}, max_x: {self._max_x}, max_z: {self._max_z}, min_z: {self._min_z}'

    def __repr__(self, *args, **kwargs):
        return f'({self})'

    def _check_sameness(self, wall: EditorWall, other_side_sector: EditorSector):
        if other_side_sector != self._other_side_sector:
            return False

        if wall == self._start_wall:
            return False

        return True

    def _check_depth(self, point: core.Point3):
        if point.z > 1:
            return False

        if point.z > self._max_z:
            self._max_z = point.z

        if point.z < self._min_z:
            self._min_z = point.z

        return True
