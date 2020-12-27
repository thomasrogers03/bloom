# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects

class IncrementSectorHeinum:

    def __init__(self, sector: map_objects.EditorSector, part: str):
        self._sector = sector
        self._part = part

    def increment(self, amount: float):
        heinum = self._sector.get_heinum(self._part)
        self._sector.set_heinum(self._part, heinum + amount)

        for wall in self._sector.portal_walls():
            wall.other_side_wall.invalidate_geometry()
