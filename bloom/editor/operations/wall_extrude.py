# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects
from . import wall_link


class WallExtrude:

    def __init__(
        self, 
        wall: map_objects.EditorWall,
        all_sectors: map_objects.SectorCollection
    ):
        self._wall = wall
        self._all_sectors = all_sectors

    def extrude(self):
        if self._wall.other_side_wall is not None:
            return

        new_sector = self._all_sectors.create_sector(self._sector)
        extrude_direction = self._wall.get_normal() * 2048

        blood_point_1 = self._blood_wall.copy()
        blood_point_1.wall.position_x = self._blood_wall_point_2.wall.position_x
        blood_point_1.wall.position_y = self._blood_wall_point_2.wall.position_y
        point_1 = new_sector.add_wall(blood_point_1)

        blood_point_2 = self._blood_wall.copy()
        blood_point_2.wall.position_x = self._blood_wall.wall.position_x
        blood_point_2.wall.position_y = self._blood_wall.wall.position_y
        point_2 = new_sector.add_wall(blood_point_2)

        blood_point_3 = self._blood_wall.copy()
        blood_point_3.wall.position_x = int(
            self._blood_wall.wall.position_x + extrude_direction.x
        )
        blood_point_3.wall.position_y = int(
            self._blood_wall.wall.position_y + extrude_direction.y
        )
        point_3 = new_sector.add_wall(blood_point_3)

        blood_point_4 = self._blood_wall.copy()
        blood_point_4.wall.position_x = int(
            self._blood_wall_point_2.wall.position_x + extrude_direction.x
        )
        blood_point_4.wall.position_y = int(
            self._blood_wall_point_2.wall.position_y + extrude_direction.y
        )
        point_4 = new_sector.add_wall(blood_point_4)

        self._wall.link(point_1)

        point_1.wall_previous_point = point_4
        point_2.wall_previous_point = point_1
        point_3.wall_previous_point = point_2
        point_4.wall_previous_point = point_3

        new_segments = [
            (point_1, point_2),
            (point_2, point_3),
            (point_3, point_4),
            (point_4, point_1)
        ]
        for new_wall, new_wall_point_2 in new_segments:
            new_wall.setup(
                new_wall_point_2,
                None
            )
            new_wall.reset_panning_and_repeats(None)
        point_1.link(self._wall)

        for new_wall in [point_2, point_3, point_4]:
            wall_link.SectorWallLink(new_wall, self._all_sectors).try_link_wall()

        self._wall.invalidate_geometry()

    @property
    def _sector(self) -> map_objects.EditorSector:
        return self._wall.sector

    @property
    def _blood_wall(self):
        return self._wall.blood_wall

    @property
    def _wall_point_2(self):
        return self._wall.wall_point_2

    @property
    def _blood_wall_point_2(self):
        return self._wall_point_2.blood_wall
