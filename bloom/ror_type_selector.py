# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.gui import DirectGui, DirectGuiGlobals
from panda3d import core

from . import constants, edit_mode
from .edit_modes import empty_edit_mode
from .editor import map_objects, ror_constants


class RORTypeSelector(empty_edit_mode.EditMode):

    def __init__(self, parent: core.NodePath, edit_mode_selector: edit_mode.EditMode):
        self._edit_mode_selector = edit_mode_selector
        self._type_selected: typing.Optional[typing.Callable[[str], None]] = None

        self._frame = DirectGui.DirectFrame(
            parent=parent,
            pos=core.Vec3(-0.18, -0.1),
            frameSize=(0, 0.36, 0, 0.24),
            relief=DirectGuiGlobals.RAISED,
            borderWidth=(0.01, 0.01)
        )
        self._frame.hide()

        self._ror_type_selector = DirectGui.DirectOptionMenu(
            parent=self._frame,
            pos=core.Vec3(0.04, 0.14),
            scale=constants.HUGE_TEXT_SIZE,
            items=[
                ror_constants.ROR_TYPE_LINK,
                ror_constants.ROR_TYPE_STACK,
                ror_constants.ROR_TYPE_WATER,
                ror_constants.ROR_TYPE_GOO,
            ]
        )

        DirectGui.DirectButton(
            parent=self._frame,
            pos=core.Vec3(0.18, 0.05),
            frameSize=core.Vec4(-0.06, 0.06, -0.02, 0.06) / constants.BIG_TEXT_SIZE,
            scale=constants.BIG_TEXT_SIZE,
            text='Ok',
            command=self._confirm
        )

    def show(self, type_selected: typing.Callable[[str], None]):
        self._type_selected = type_selected
        self._ror_type_selector.set(ror_constants.ROR_TYPE_LINK)
        self._edit_mode_selector.push_mode(self)

    def enter_mode(self, state: dict):
        self._frame.show()

    def exit_mode(self):
        self._frame.hide()
        self._type_selected = None
        return {}

    def tick(self):
        pass

    def _confirm(self):
        result = self._ror_type_selector.get()
        if self._type_selected is not None:
            self._type_selected(result)
        self._edit_mode_selector.pop_mode()
