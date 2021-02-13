# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from ... import editor
from .. import map_objects


class WallAlign:
    def __init__(self, first_wall: map_objects.EditorWall):
        self._first_wall = first_wall

    def align(self):
        with self._first_wall.undos.multi_step_undo("Wall Align"):
            self._do_align(set())

    def _do_align(self, seen: typing.Set[map_objects.EditorWall]):
        if self._first_wall in seen:
            return

        picnum = self._first_wall.blood_wall.wall.picnum

        seen.add(self._first_wall)
        walls_for_alignment: typing.List[map_objects.EditorWall] = []

        previous_wall = self._first_wall
        current_wall = previous_wall.wall_point_2
        while current_wall != self._first_wall:
            current_wall.invalidate_geometry()
            seen.add(current_wall)

            new_panning_x = previous_wall.x_panning + previous_wall.x_repeat
            new_panning_y = previous_wall.y_panning + previous_wall.y_repeat

            for wall_to_update in current_wall.all_walls_at_point_1():
                if wall_to_update.blood_wall.wall.picnum != picnum:
                    continue

                with wall_to_update.change_blood_object():
                    wall_to_update.blood_wall.wall.panning_x = (
                        editor.to_build_panning_x(new_panning_x)
                    )
                    wall_to_update.blood_wall.wall.panning_y = (
                        editor.to_build_panning_y(new_panning_y)
                    )

                if wall_to_update != current_wall:
                    walls_for_alignment.append(wall_to_update)

            previous_wall = current_wall
            current_wall = current_wall.wall_point_2

        for additional_wall in walls_for_alignment:
            WallAlign(additional_wall)._do_align(seen)
