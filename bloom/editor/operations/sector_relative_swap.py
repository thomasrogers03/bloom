# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects

class SectorRelativeSwap:

    def __init__(self, sector: map_objects.EditorSector, part: str):
        self._sector = sector
        self._stat = self._sector.get_stat_for_part(part)

    def toggle(self):
        self._sector.invalidate_geometry()
        self._stat.align = (self._stat.align + 1) % 2