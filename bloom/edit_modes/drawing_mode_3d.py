# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0



from panda3d import bullet, core

from .. import clicker, constants
from ..editor import operations
from ..editor.map_objects.sector import EditorSector
from ..utils import shapes
from . import drawing_display, navigation_mode_3d, sector_drawer


class EditMode(navigation_mode_3d.EditMode):

    def __init__(
        self,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._sector_drawer = sector_drawer.SectorDrawer(
            self._camera_collection,
            self._tickers,
            self._make_clicker,
            self._extrude_mouse_to_scene_transform
        )

    def start_drawing(self, sector: EditorSector, hit_point: core.Point3, insert: bool):
        self._sector_drawer.start_drawing(self._editor, sector, hit_point, insert)
        self._edit_mode_selector.push_mode(self)

    def enter_mode(self, state: dict):
        super().enter_mode(state)
        self._sector_drawer.show(self, self._edit_mode_selector.pop_mode)

    def exit_mode(self):
        self._sector_drawer.hide()
        return super().exit_mode()
