# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

from .. import map_objects

class WallDelete:

    def __init__(self, wall: map_objects.EditorWall):
        self._wall = wall

    def delete(self):
        if self._wall.is_destroyed:
            return

        self._sector.remove_wall(self._wall)
        self._previous_wall.set_wall_point_2(self._next_wall)
        self._next_wall.wall_previous_point = self._previous_wall
        self._wall.destroy()

        if self._other_side_wall is not None:
            self._other_side_wall.unlink()

            other_side_remove_wall = self._other_side_wall.wall_point_2
            if other_side_remove_wall.other_side_wall is not None:
                self._other_side_wall.link(other_side_remove_wall.other_side_wall)
                other_side_remove_wall.other_side_wall.link(
                    self._other_side_wall, 
                    force=True
                )
            self._other_side_wall.set_wall_point_2(other_side_remove_wall.wall_point_2)
            other_side_remove_wall.wall_point_2.wall_previous_point = self._other_side_wall
            self._other_side_wall.sector.remove_wall(other_side_remove_wall)
            other_side_remove_wall.destroy()

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