# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math

from panda3d import core

from .. import editor


class GridSnapper:

    def __init__(self):
        self._grid_size = 256
        self._angular_grid_size = 15

    @property
    def grid_size(self):
        return self._grid_size

    def decrease_grid(self):
        self._grid_size /= 2
        if self._grid_size < 1:
            self._grid_size = 1

    def increase_grid(self):
        self._grid_size *= 512
        if self._grid_size > 512:
            self._grid_size = 512

    def snap_to_grid(self, value: float):
        return editor.snap_to_grid(value, self._grid_size)

    def snap_to_grid_2d(self, value: core.Vec2):
        x = self.snap_to_grid(value.x)
        y = self.snap_to_grid(value.y)

        return core.Vec2(x, y)

    def snap_to_grid_3d(self, value: core.Vec3):
        x = self.snap_to_grid(value.x)
        y = self.snap_to_grid(value.y)
        z = self.snap_to_grid(value.z)

        return core.Vec3(x, y, z)

    def snap_to_angular_grid(self, value: float):
        return editor.snap_to_grid(value, self._angular_grid_size)

    def snap_to_angular_grid_2d_scaled(self, direction: core.Vec2):
        return self.snap_to_angular_grid_2d(direction) * direction.length()

    def snap_to_angular_grid_2d(self, direction: core.Vec2):
        theta = math.atan2(direction.y, direction.x)
        
        theta = self.snap_to_angular_grid(math.degrees(theta))
        cos_theta = math.cos(math.radians(theta))
        sin_theta = math.sin(math.radians(theta))

        return core.Vec2(cos_theta, sin_theta)
