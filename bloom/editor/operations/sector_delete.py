# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects

class SectorDelete:

    def __init__(
        self, 
        sector: map_objects.EditorSector, 
        all_sectors: map_objects.SectorCollection
    ):
        self._sector = sector
        self._all_sectors = all_sectors

    def delete(self):
        for wall in self._sector.portal_walls():
            wall.other_side_wall.unlink()
            wall.destroy()
        self._all_sectors.destroy_sector(self._sector)
