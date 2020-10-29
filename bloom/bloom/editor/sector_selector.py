# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from . import empty_selector, grid_snapper
from .sector import EditorSector


class Selector(empty_selector.Selector):

    def __init__(self, scene: core.NodePath, sector: EditorSector, part: str, snapper: grid_snapper.GridSnapper):
        self._sector = sector
        self._part = part
        self._snapper = snapper
        self._start_height: float = None

    def get_selected(self):
        return self._sector

    def get_picnum(self):
        return self._sector.get_picnum(self._part)

    def set_picnum(self, picnum: int):
        self._sector.set_picnum(self._part, picnum)

    def begin_move(self, hit: core.Point3):
        if self._start_height is None:
            if self._part == 'floor_collision':
                self._start_height = self._sector.floor_z
            else:
                self._start_height = self._sector.ceiling_z

    def end_move(self):
        self._start_height = None

    def move(
        self,
        total_delta: core.Vec2,
        delta: core.Vec2,
        total_camera_delta: core.Vec2,
        camera_delta: core.Vec2,
        modified: bool
    ):
        new_height = self._snapper.snap_to_grid(self._start_height - total_delta.y)

        if self._part == 'floor_collision':
            self._sector.move_floor_to(new_height)
        else:
            self._sector.move_ceiling_to(new_height)
