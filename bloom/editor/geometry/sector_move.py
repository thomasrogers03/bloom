# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import grid_snapper
from ..map_objects.sector import EditorSector
from . import empty_move


class SectorMove(empty_move.EmptyMove):

    def __init__(self, sector: EditorSector, part: str):
        self._sector = sector
        self._part = part

        if self._part == EditorSector.FLOOR_PART:
            self._start_z = self._sector.floor_z
        else:
            self._start_z = self._sector.ceiling_z

    def get_move_direction(self) -> core.Vec3:
        return core.Vec3(0, 0, -1)

    def move(self, move_delta: core.Vec3):
        new_z = self._start_z + move_delta.z
        if self._part == EditorSector.FLOOR_PART:
            self._sector.move_floor_to(new_z)
        else:
            self._sector.move_ceiling_to(new_z)
