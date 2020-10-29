# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0



from panda3d import core

from .. import clicker
from . import navigation_mode_3d
from ..editor.sector import EditorSector


class EditMode(navigation_mode_3d.EditMode):

    def __init__(
        self,
        camera: core.NodePath,
        lens: core.Lens,
        *args,
        **kwargs
    ):
        super().__init__(camera, lens, *args, **kwargs)
        self._sector: EditorSector = None

        self._make_clicker(
            [core.MouseButton.one()],
            on_click=self._insert_point,
        )

    def start_drawing(self, sector: EditorSector):
        self._sector = sector
        self._edit_mode_selector.push_mode(self)

    def _insert_point(self):
        pass
