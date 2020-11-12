# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


import math

from panda3d import core

from .. import clicker, constants
from . import base_edit_mode, keyboard_camera


class EditMode(base_edit_mode.EditMode):

    def __init__(
        self,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._mouse_watcher = self._edit_mode_selector.mouse_watcher

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

    def enter_mode(self):
        super().enter_mode()
        keyboard_camera.KeyboardCamera(
            self._camera_collection,
            self._editor,
            self.accept
        )

    def _extrude_mouse_to_scene_transform(self, check_buttons=False):
        if not self._mouse_watcher.has_mouse():
            return None, None

        if check_buttons and any(self._mouse_watcher.is_button_down(button) for button in clicker.Clicker.ALL_MOUSE_BUTTONS):
            return None, None

        mouse = self._mouse_watcher.get_mouse()
        source = core.Point3()
        target = core.Point3()

        self._camera.lens.extrude(mouse, source, target)

        source = self._camera_collection.scene.get_relative_point(self._camera.camera, source)
        target = self._camera_collection.scene.get_relative_point(self._camera.camera, target)

        return source, target

    def _pan_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        self._camera_collection.pan_camera(delta)
        self._editor.update_builder_sector(self._camera_collection.get_builder_position())

    def _strafe_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        self._camera_collection.strafe_camera(delta)
        self._editor.update_builder_sector(self._camera_collection.get_builder_position())

    def _rotate_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        self._camera_collection.rotate_camera(delta)
        self._editor.invalidate_view_clipping()

    @property
    def _camera(self):
        return self._camera_collection['default']
