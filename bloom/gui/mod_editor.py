# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.gui import DirectGui, DirectGuiGlobals
from panda3d import core

from .. import addon, audio, edit_mode
from ..editor import map_editor


class ModEditor:
    def __init__(
        self,
        parent: core.NodePath,
        edit_mode_selector: edit_mode.EditMode,
        audio_manager: audio.Manager,
        get_addons: typing.Callable[[], typing.List[addon.Addon]],
    ):
        self._edit_mode_selector = edit_mode_selector
        self._audio_manager = audio_manager
        self._get_addons = get_addons
        self._addons: typing.List[addon.Addon] = []
        self._editor: map_editor.MapEditor = None
        self._map_path: str = None

        self._dialog = DirectGui.DirectFrame(
            parent=parent,
            pos=core.Vec3(-1.1, -0.9),
            frameSize=(0, 2.2, 0, 1.8),
            relief=DirectGuiGlobals.RAISED,
            borderWidth=(0.01, 0.01),
        )
        self._dialog.hide()

    def show(self, editor: map_editor.MapEditor, map_path: str):
        self._editor = editor
        self._map_path = map_path
        self._edit_mode_selector.push_mode(self)

    def enter_mode(self, state: dict):
        self._addons = self._get_addons()
        self._dialog.show()

    def exit_mode(self):
        self._dialog.hide()
        return {}

    def _hide(self):
        self._edit_mode.pop_mode()

    def tick(self):
        pass
