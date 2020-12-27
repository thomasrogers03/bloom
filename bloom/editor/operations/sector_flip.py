# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects
from . import wall_split


class SectorFlip:

    def __init__(
        self,
        sectors: typing.List[map_objects.EditorSector]
    ):
        self._sectors = sectors

    def flip(self, vertical: bool, horizontal: bool):
        if len(self._sectors) < 1:
            return

        sector_set = set(self._sectors)
        first_point = self._sectors[0].walls[0].origin_2d

        for sector in self._sectors:
            sector.invalidate_geometry()

            old_previous_points: typing.Dict[
                map_objects.EditorWall,
                map_objects.EditorWall
            ] = {}

            for wall in sector.walls:
                if wall.other_side_sector is not None and \
                        wall.other_side_sector not in sector_set:
                    wall.unlink()

                new_position = wall.origin_2d
                offset = new_position - first_point

                if horizontal:
                    new_position.x = first_point.x - offset.x
                if vertical:
                    new_position.y = first_point.y - offset.y
                wall.teleport_point_1_to(new_position)
                old_previous_points[wall.wall_point_2] = wall

            if vertical ^ horizontal:
                for wall in sector.walls:
                    new_point_2 = old_previous_points[wall]
                    wall.set_wall_point_2(new_point_2)

            for sprite in sector.sprites:
                new_position = sprite.origin
                offset = new_position.xy - first_point

                if horizontal:
                    new_position.x = first_point.x - offset.x
                if vertical:
                    new_position.y = first_point.y - offset.y
                sprite.move_to(new_position)

        if vertical ^ horizontal:
            relinked_walls: typing.Set[map_objects.EditorWall] = set()
            for sector in self._sectors:
                for wall in sector.walls:
                    if wall not in relinked_walls and wall.other_side_wall is not None:
                        other_side_wall = wall.other_side_wall
                        wall.unlink()

                        relinked_walls.add(wall.wall_previous_point)
                        relinked_walls.add(other_side_wall.wall_previous_point)
                        wall.wall_previous_point.link(other_side_wall.wall_previous_point)

