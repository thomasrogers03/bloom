# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math

from panda3d import core

from .. import constants
from . import base_edit_mode


class EditMode(base_edit_mode.EditMode):

    def __init__(self, camera_2d: core.NodePath, display_region: core.DisplayRegion, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._camera_2d = camera_2d
        self._display_region = display_region

        self._make_clicker(
            [core.MouseButton.one()],
            on_click_move=self._pan_camera_2d,
        )

        self._make_clicker(
            [core.MouseButton.one(), core.MouseButton.three()],
            on_click_move=self._strafe_camera_2d,
        )

    def enter_mode(self):
        super().enter_mode()
        self.accept('tab', lambda: self._edit_mode_selector.pop_mode())
        self._display_region.set_active(True)

    def exit_mode(self):
        super().exit_mode()
        self._display_region.set_active(False)

    def _pan_camera_2d(self, total_delta: core.Vec2, delta: core.Vec2):
        x_direction = (delta.x * self._camera_2d.get_sx()) / 50
        y_direction = (delta.y * self._camera_2d.get_sx()) / 50

        self._builder_camera_2d.set_x(
            self._builder_camera_2d, 
            x_direction * constants.TICK_SCALE
        )
        self._builder_camera_2d.set_y(
            self._builder_camera_2d, y_direction * constants.TICK_SCALE)

    def _strafe_camera_2d(self, total_delta: core.Vec2, delta: core.Vec2):
        delta *= constants.TICK_SCALE / 100.0

        scale_grid = 1.0 / 8
        delta_y_scaled = delta.y / 2
        zoom_amount = int(delta_y_scaled / scale_grid) * scale_grid

        zoom_scale = math.pow(2, zoom_amount)
        current_zoom = self._camera_2d.get_sx()
        new_zoom = current_zoom * zoom_scale

        if new_zoom > 128:
            new_zoom = 128
        if new_zoom < 1:
            new_zoom = 1

        self._camera_2d.set_scale(new_zoom)
        self._builder_camera_2d.set_x(self._builder_camera_2d, delta.x * 512)