# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0


from direct.gui import DirectGui, DirectGuiGlobals
from direct.task import Task
from panda3d import core

from . import audio, constants, edit_mode, ror_type_selector, tile_dialog
from .audio import sound_view
from .editor import properties
from .tiles import manager
from .utils import gui


class Dialogs:
    
    def __init__(
        self,
        parent: core.NodePath,
        tile_manager: manager.Manager,
        edit_mode_selector: edit_mode.EditMode,
        audio_manager: audio.Manager,
        task_manager: Task.TaskManager
    ):
        self._tile_dialog = tile_dialog.TileDialog(
            parent,
            tile_manager,
            edit_mode_selector,
            task_manager
        )
        self._sound_view = sound_view.SoundView(
            parent,
            audio_manager,
            task_manager,
            edit_mode_selector
        )
        self._sprite_properties = properties.sprite_properties.SpriteDialog(
            parent,
            edit_mode_selector,
            task_manager,
            self._sound_view,
            self._tile_dialog
        )
        self._wall_properties = properties.wall_properties.WallDialog(
            parent,
            edit_mode_selector
        )
        self._ror_type_selector = ror_type_selector.RORTypeSelector(
            parent,
            edit_mode_selector
        )

    @property
    def tile_dialog(self):
        return self._tile_dialog

    @property
    def sprite_properties(self):
        return self._sprite_properties

    @property
    def wall_properties(self):
        return self._wall_properties

    @property
    def sound_view(self):
        return self._sound_view

    @property
    def ror_type_selector(self):
        return self._ror_type_selector
