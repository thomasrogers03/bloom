# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0



from panda3d import core

from .. import clicker, constants
from ..editor.highlighting import highlight_finder_3d
from . import base_edit_mode, keyboard_camera


class EditMode(base_edit_mode.EditMode):

    def __init__(
        self,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        
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

    def enter_mode(self, state: dict):
        super().enter_mode(state)
        keyboard_camera.KeyboardCamera(
            self._camera_collection,
            self._editor,
            self.accept
        )

    def _pan_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        self._camera_collection.pan_camera(delta)
        self._editor.update_builder_sector(self._camera_collection.get_builder_position())

    def _strafe_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        self._camera_collection.strafe_camera(delta)
        self._editor.update_builder_sector(self._camera_collection.get_builder_position())

    def _rotate_camera(self, total_delta: core.Vec2, delta: core.Vec2):
        self._camera_collection.rotate_camera(delta)
        self._editor.invalidate_view_clipping()

    def _make_highlight_finder_callback(self):
        source, target = self._extrude_mouse_to_scene_transform(check_buttons=True)
        if source is None or target is None:
            return lambda highlight, _: highlight

        return highlight_finder_3d.HighlightFinder3D(self._editor, source, target).find_highlight

    @property
    def _camera(self):
        return self._camera_collection['default']
