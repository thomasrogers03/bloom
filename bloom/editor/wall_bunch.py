# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .map_objects.sector import EditorSector
from .map_objects.wall import EditorWall


class ProjectedWall:
    def __init__(
        self, wall: EditorWall, project_point: typing.Callable[[core.Vec2], core.Point3]
    ):
        self.wall = wall
        self._point: core.Point3 = project_point(self.wall.point_1)
        self.previous_wall: ProjectedWall = None
        self.next_wall: ProjectedWall = None

    @property
    def point_1(self):
        return self._point

    @property
    def point_2(self):
        return self.next_wall.point_1


class WallBunch:
    ABSOLUTE_MIN_X = -1.125
    ABSOLUTE_MAX_X = 1.125
    WIDTH_RANGE = ABSOLUTE_MAX_X - ABSOLUTE_MIN_X
    ABSOLUTE_MAX_Z = 1

    def __init__(self, start_wall: ProjectedWall):
        self._start_wall = start_wall
        self._editor_walls_previous: typing.List[EditorWall] = []
        self._editor_walls_next: typing.List[EditorWall] = [start_wall.wall]

        self._other_side_sector: EditorSector = None
        if self._start_wall.wall.is_other_side_sector_visible():
            self._other_side_sector: EditorSector = (
                self._start_wall.wall.other_side_sector
            )

        self._no_more_previous = False
        self._no_more_next = False

        self._min_x = self._start_wall.point_1.x
        self._max_x = self._start_wall.point_2.x

        if self._start_wall.point_1.z >= self.ABSOLUTE_MAX_Z:
            self._min_x = self.ABSOLUTE_MIN_X
            self._max_z = self._start_wall.point_2.z
            self._min_z = self._start_wall.point_2.z

            self._no_more_previous = True
        elif self._start_wall.point_2.z >= self.ABSOLUTE_MAX_Z:
            self._max_x = self.ABSOLUTE_MAX_X
            self._max_z = self._start_wall.point_1.z
            self._min_z = self._start_wall.point_1.z

            self._no_more_next = True
            self._editor_walls_next.append(self._start_wall.wall)
        else:
            self._max_z = max(self._start_wall.point_1.z, self._start_wall.point_2.z)
            self._min_z = min(self._start_wall.point_1.z, self._start_wall.point_2.z)

        if self._min_x > self._max_x:
            self._no_more_previous = True
            self._no_more_next = True

    @property
    def left(self):
        return max(self._min_x, self.ABSOLUTE_MIN_X)

    @property
    def right(self):
        return min(self._max_x, self.ABSOLUTE_MAX_X)

    @property
    def depth(self):
        return min(self._max_z, self.ABSOLUTE_MAX_Z)

    @property
    def editor_walls_previous(self):
        return self._editor_walls_previous

    @property
    def editor_walls_next(self):
        return self._editor_walls_next

    @property
    def editor_walls(self) -> typing.List[EditorWall]:
        return self._editor_walls_previous + self._editor_walls_next

    @property
    def other_side_sector(self):
        return self._other_side_sector

    def add_wall_previous(self, wall: ProjectedWall) -> bool:
        if self._no_more_previous:
            return False

        if not self._check_sameness(wall, wall.wall.other_side_sector):
            return False

        if not self._check_depth(wall.point_1):
            self._no_more_previous = True
            self._min_x = self.ABSOLUTE_MIN_X
            self._editor_walls_previous.append(wall.wall)
            return False

        if wall.point_1.x > self._min_x:
            return False

        self._min_x = wall.point_1.x
        self._editor_walls_previous.append(wall.wall)
        return True

    def add_wall_next(self, wall: ProjectedWall) -> bool:
        if self._no_more_next:
            return False

        if not self._check_sameness(wall, wall.previous_wall.wall.other_side_sector):
            return False

        if not self._check_depth(wall.point_1):
            self._no_more_next = True
            self._max_x = self.ABSOLUTE_MAX_X
            return False

        if wall.point_1.x < self._max_x:
            return False

        self._max_x = wall.point_1.x
        self._editor_walls_next.append(wall.previous_wall.wall)
        return True

    def __str__(self, *args, **kwargs):
        return f"portal_sector: {self._other_side_sector}, min_x: {self._min_x}, max_x: {self._max_x}, max_z: {self._max_z}, min_z: {self._min_z}"

    def __repr__(self, *args, **kwargs):
        return f"({self})"

    def _check_sameness(self, wall: ProjectedWall, other_side_sector: EditorSector):
        if other_side_sector != self._other_side_sector:
            return False

        if wall == self._start_wall:
            return False

        return True

    def _check_depth(self, point: core.Point3):
        if point.z >= self.ABSOLUTE_MAX_Z:
            return False

        if point.z > self._max_z:
            self._max_z = point.z

        if point.z < self._min_z:
            self._min_z = point.z

        return True
