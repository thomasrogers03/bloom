# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from ... import map_data
from .. import map_objects
from ..map_objects.drawing import sector as drawing_sector
from . import sector_draw, sprite_find_sector


class GradientHeights:

    def __init__(self, sectors: typing.List[map_objects.EditorSector], part: str):
        self._sectors = sectors
        self._part = part

    def apply(self):
        if len(self._sectors) < 3:
            return

        step_count = len(self._sectors) - 1
        if self._part == map_objects.EditorSector.FLOOR_PART:
            first_height = self._sectors[0].floor_z
            last_height = self._sectors[-1].floor_z

            step_height = (last_height - first_height) / step_count
            for index, sector in enumerate(self._sectors[1:-1]):
                sector.move_floor_to(first_height + step_height * (index + 1))
        else:
            first_height = self._sectors[0].ceiling_z
            last_height = self._sectors[-1].ceiling_z

            step_height = (last_height - first_height) / step_count
            for index, sector in enumerate(self._sectors[1:-1]):
                sector.move_ceiling_to(first_height + step_height * (index + 1))
