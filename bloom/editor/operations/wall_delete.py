# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects
from ..geometry import wall_repeat_adjust


class WallDelete:
    def __init__(self, wall: map_objects.EditorWall):
        self._wall = wall

    def delete(self):
        if self._wall.is_destroyed:
            return

        self._sector.remove_wall(self._wall)

        adjust = wall_repeat_adjust.WallRepeatAdjust(self._previous_wall)
        self._previous_wall.set_wall_point_2(self._next_wall)
        adjust.adjust()

        self._next_wall.wall_previous_point = self._previous_wall
        self._wall.destroy()

        if self._other_side_wall is not None:
            other_side_wall = self._other_side_wall
            self._other_side_wall.unlink()

            other_side_remove_wall = other_side_wall.wall_point_2
            if other_side_remove_wall.other_side_wall is not None:
                other_side_wall.link(other_side_remove_wall.other_side_wall)

                adjust = wall_repeat_adjust.WallRepeatAdjust(other_side_wall)
                other_side_wall.set_wall_point_2(other_side_remove_wall.wall_point_2)
                adjust.adjust()

                other_side_remove_wall.wall_point_2.wall_previous_point = (
                    other_side_wall
                )
                other_side_wall.sector.remove_wall(other_side_remove_wall)
                other_side_remove_wall.destroy()
            else:
                other_side_remove_wall.teleport_point_1_to(self._previous_wall.point_1)
                other_side_wall.link(self._previous_wall)
        elif self._previous_wall.other_side_wall is not None:
            self._previous_wall.other_side_wall.teleport_point_1_to(self._wall.point_2)

    @property
    def _other_side_wall(self) -> map_objects.EditorWall:
        return self._wall.other_side_wall

    @property
    def _previous_wall(self) -> map_objects.EditorWall:
        return self._wall.wall_previous_point

    @property
    def _next_wall(self) -> map_objects.EditorWall:
        return self._wall.wall_point_2

    @property
    def _sector(self) -> map_objects.EditorSector:
        return self._wall.sector
