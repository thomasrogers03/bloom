# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math

from panda3d import core

from .. import cameras, constants, dialogs
from ..editor import highlighter, map_objects
from ..editor.highlighting import find_in_marquee, highlight_finder_2d
from . import base_edit_mode, keyboard_camera, moving_clicker, object_editor, wall_bevel


class EditMode(base_edit_mode.EditMode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._make_clicker(
            [core.MouseButton.one()],
            on_click_move=self._pan_camera_2d,
        )

        self._make_clicker(
            [core.MouseButton.one(), core.MouseButton.three()],
            on_click_move=self._strafe_camera_2d,
        )

    def enter_mode(self, state: dict):
        super().enter_mode(state)
        self._camera.display_region.set_active(True)

        keyboard_camera.KeyboardCamera(
            self._camera_collection, self._editor, self.accept
        )

    def exit_mode(self):
        self._camera.display_region.set_active(False)
        return super().exit_mode()

    def _pan_camera_2d(self, total_delta: core.Vec2, delta: core.Vec2):
        x_direction = (self._scale_x(delta.x) * self._camera.camera.get_sx()) / 50
        y_direction = (delta.y * self._camera.camera.get_sx()) / 50

        self._camera_collection.builder_2d.set_x(
            self._camera_collection.builder_2d, x_direction * constants.TICK_SCALE
        )
        self._camera_collection.builder_2d.set_y(
            self._camera_collection.builder_2d, y_direction * constants.TICK_SCALE
        )

        self._editor.update_builder_sector(
            self._camera_collection.get_builder_position()
        )

    def _strafe_camera_2d(self, total_delta: core.Vec2, delta: core.Vec2):
        delta *= constants.TICK_SCALE / 100.0
        delta.x = self._scale_x(delta.x)

        scale_grid = 1.0 / 8
        delta_y_scaled = delta.y / 2
        zoom_amount = int(delta_y_scaled / scale_grid) * scale_grid

        zoom_scale = math.pow(2, zoom_amount)
        current_zoom = self._camera.camera.get_sx()
        new_zoom = current_zoom * zoom_scale

        if new_zoom > 512:
            new_zoom = 512
        if new_zoom < 1:
            new_zoom = 1

        self._camera.camera.set_scale(new_zoom)
        self._camera_collection.builder_2d.set_x(
            self._camera_collection.builder_2d, delta.x * 512
        )

        self._editor.update_builder_sector(
            self._camera_collection.get_builder_position()
        )

    def _scale_x(self, value: float):
        inverse_aspect_ratio = 1.0 / self._camera_collection.aspect_2d.get_sx()
        return value * inverse_aspect_ratio

    @property
    def _camera(self) -> cameras.Camera:
        return self._camera_collection["editor_2d"]
