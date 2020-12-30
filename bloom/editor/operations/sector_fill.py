# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from ... import map_data
from .. import map_objects
from ..map_objects.drawing import sector as drawing_sector
from . import sector_draw, sprite_find_sector


class SectorFill:

    def __init__(self, sector_to_split: map_objects.EditorSector, all_sectors: map_objects.SectorCollection):
        self._sector_to_split = sector_to_split
        self._all_sectors = all_sectors

    def fill(
        self,
        start_wall: map_objects.EditorWall
    ):
        if not drawing_sector.Sector.is_sector_section_clockwise(start_wall):
            return False

        walls: typing.List[map_objects.EditorWall] = list(start_wall.iterate_wall_bunch())
        for wall in walls:
            if wall.other_side_wall is not None:
                return False

        new_sector = self._all_sectors.create_sector(self._sector_to_split)
        new_walls: typing.List[map_objects.EditorWall] = []

        for wall in reversed(walls):
            new_wall = new_sector.add_wall(wall.blood_wall.copy())
            new_walls.append(new_wall)

        segments = zip(new_walls, new_walls[1:] + [new_walls[0]])
        for wall, wall_point_2 in segments:
            wall.set_wall_point_2(wall_point_2)

        new_walls = list(reversed(new_walls))
        otherside_walls = new_walls[1:] + new_walls[:1]
        for editor_wall, otherside_wall in zip(walls, otherside_walls):
            editor_wall.link(otherside_wall)

        return True