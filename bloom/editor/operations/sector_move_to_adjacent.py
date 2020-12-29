# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from ... import constants
from .. import map_objects


class SectorMoveToAdjacent:

    def __init__(self, sector: map_objects.EditorSector, part: str):
        self._sector = sector
        self._part = part

    def move(self, move_up: bool):
        found = False
        if self._part == map_objects.EditorSector.FLOOR_PART:
            floor_z = self._sector.floor_z
            highest = constants.REALLY_BIG_NUMBER
            for portal in self._sector.portal_walls():
                new_z = portal.other_side_sector.floor_z
                if new_z > floor_z and new_z < highest:
                    highest = new_z
                    found = True

            if found:
                self._sector.move_floor_to(highest)
        else:
            ceiling_z = self._sector.ceiling_z
            lowest = -constants.REALLY_BIG_NUMBER
            for portal in self._sector.portal_walls():
                new_z = portal.other_side_sector.ceiling_z
                if new_z < ceiling_z and new_z > lowest:
                    lowest = new_z
                    found = True

            if found:
                self._sector.move_ceiling_to(lowest)
