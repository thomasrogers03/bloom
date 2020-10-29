# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


import math

from panda3d import core

from .. import constants
from . import base_edit_mode


class EditMode(base_edit_mode.EditMode):

    def __init__(
        self,
        camera: core.NodePath,
        lens: core.Lens,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

        self._camera = camera
        self._lens = lens

        self._make_clicker(
            [core.MouseButton.one()],
            on_click_move=self._pan_camera,
        )

        self._make_clicker(
            [core.MouseButton.three()],
            on_click_move=self._rotate_camera,
        )

        self._make_clicker(
            [core.MouseButton.one(), core.MouseButton.three()],
            on_click_move=self._strafe_camera,
        )

    def _pan_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        heading = self._builder_camera.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))
        x_direction = -sin_theta * delta.y + cos_theta * delta.x
        y_direction = cos_theta * delta.y + sin_theta * delta.x

        self._builder_camera_2d.set_x(
            self._builder_camera_2d, x_direction * constants.TICK_SCALE)
        self._builder_camera_2d.set_y(
            self._builder_camera_2d, y_direction * constants.TICK_SCALE)

    def _strafe_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        delta *= 100

        heading = self._builder_camera.get_h()

        sin_theta = math.sin(math.radians(heading))
        cos_theta = math.cos(math.radians(heading))
        x_direction = cos_theta * delta.x
        y_direction = sin_theta * delta.x

        self._builder_camera.set_z(self._builder_camera.get_z() + delta.y * 512)

        self._builder_camera_2d.set_x(self._builder_camera_2d, x_direction * 512)
        self._builder_camera_2d.set_y(self._builder_camera_2d, y_direction * 512)

    def _rotate_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        hpr = self._builder_camera.get_hpr()
        hpr = core.Vec3(hpr.x - delta.x * 90, hpr.y + delta.y * 90, 0)

        if hpr.y < -90:
            hpr.y = -90
        if hpr.y > 90:
            hpr.y = 90

        self._builder_camera.set_hpr(hpr)
