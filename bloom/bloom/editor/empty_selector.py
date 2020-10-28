# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core


class Selector:

    def get_picnum(self):
        return -1

    def set_picnum(self, picnum: int):
        pass

    def begin_move(self, hit: core.Point3):
        pass

    def end_move(self):
        pass

    def move(
        self,
        total_delta: core.Vec2,
        delta: core.Vec2,
        total_camera_delta: core.Vec2,
        camera_delta: core.Vec2,
        modified: bool
    ):
        pass
