# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects
from . import wall_split


class SectorCopy:
    def __init__(
        self,
        sectors: typing.List[map_objects.EditorSector],
        all_sectors: map_objects.SectorCollection,
    ):
        self._sectors = sectors
        self._all_sectors = all_sectors

    def copy(self, copy_to: core.Point2):
        result: typing.List[map_objects.EditorSector] = []
        if len(self._sectors) < 1:
            return result

        new_walls: typing.Dict[map_objects.EditorWall, map_objects.EditorWall] = {}

        first_point = self._sectors[0].walls[0].origin_2d
        offset_2d = copy_to - first_point
        offset = core.Vec3(offset_2d.x, offset_2d.y, 0.0)

        for sector in self._sectors:
            new_sector = self._all_sectors.create_sector(sector)
            result.append(new_sector)

            for wall in sector.walls:
                blood_wall = wall.blood_wall.copy()
                new_wall = new_sector.add_wall(blood_wall)
                new_wall.teleport_point_1_to(new_wall.point_1 + offset_2d)
                new_walls[wall] = new_wall

            for wall in sector.walls:
                new_wall = new_walls[wall]
                new_wall_point_2 = new_walls[wall.wall_point_2]
                new_wall.set_wall_point_2(new_wall_point_2)

            for sprite in sector.sprites:
                blood_sprite = sprite.sprite.copy()
                new_sprite = new_sector.add_sprite(blood_sprite)
                new_sprite.move_to(new_sprite.position + offset)

        for sector in self._sectors:
            for wall in sector.walls:
                if wall.other_side_wall in new_walls:
                    new_wall = new_walls[wall]
                    if new_wall.other_side_wall is None:
                        new_other_side_wall = new_walls[wall.other_side_wall]
                        new_wall.link(new_other_side_wall)

        return result
