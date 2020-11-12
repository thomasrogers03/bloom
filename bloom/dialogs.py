# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from direct.gui import DirectGui, DirectGuiGlobals
from direct.task import Task
from panda3d import core

from . import constants, edit_mode, tile_dialog
from .editor import properties
from .tiles import manager
from .utils import gui


class Dialogs:
    
    def __init__(
        self,
        parent: core.NodePath,
        tile_manager: manager.Manager,
        edit_mode: edit_mode.EditMode,
        task_manager: Task.TaskManager
    ):
        self._tile_dialog = tile_dialog.TileDialog(
            parent,
            tile_manager,
            edit_mode,
            task_manager
        )
        self._sprite_properties = properties.sprite_properties.SpriteDialog(
            parent,
            edit_mode,
            task_manager,
            self._tile_dialog
        )

    @property
    def tile_dialog(self):
        return self._tile_dialog

    @property
    def sprite_properties(self):
        return self._sprite_properties
