# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from ..map_objects import sector


class SectorJoin:

    def __init__(self, joiner: sector.EditorSector, joinee: sector.EditorSector):
        self._joiner = joiner
        self._joinee = joinee

    @property
    def _walls(self):
        return self._joiner.walls

    @property
    def _sprites(self):
        return self._joiner.sprites

    def join(self):
        adjoining = False
        for editor_wall in self._walls:
            if editor_wall.other_side_sector == self._joinee:
                adjoining = True
                break

        if not adjoining:
            return

        self._joiner.validate()
        self._joinee.validate()

        wall_count = len(self._walls)
        index = 0
        while index < wall_count:
            editor_wall = self._walls[index]
            if editor_wall.other_side_sector == self._joinee:
                editor_wall.destroy()
                del self._walls[index]
                index -= 1
                wall_count -= 1
            index += 1

        for editor_wall in self._joinee._walls:
            if editor_wall.other_side_sector == self._joiner:
                editor_wall.destroy()

        for editor_wall in self._joinee.walls:
            if not editor_wall.is_destroyed:
                self._walls.append(editor_wall)

        for editor_sprite in self._joinee.sprites:
            self._sprites.append(editor_sprite)
            editor_sprite.move_to_sector(self._joiner)

        for wall_index, editor_wall in enumerate(self._walls):
            editor_wall.set_sector(self._joiner, wall_index)

        for editor_wall in self._walls:
            next_point = editor_wall.point_2

            if editor_wall.wall_point_2.is_destroyed:
                found = False
                for find_wall in self._walls:
                    if next_point == find_wall.point_1:
                        assert(find_wall.wall_previous_point.is_destroyed)

                        find_wall.wall_previous_point = editor_wall
                        editor_wall.set_wall_point_2(find_wall)
                        found = True
                        break
                assert(found)

        self._joiner.validate()
        self._joiner.invalidate_geometry()

        self._joinee.destroy()

