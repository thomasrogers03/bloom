# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import grid_snapper, highlighter, map_objects, operations
from . import empty_move, sector_move, sprite_move, wall_move


class Move:

    def __init__(
        self,
        selected_objects: typing.List[highlighter.HighlightDetails],
        highlighted_object: highlighter.HighlightDetails,
        snapper: grid_snapper.GridSnapper,
        all_sectors: map_objects.SectorCollection
    ):
        self._hit = highlighted_object.hit_position
        self._highlighted_mover = self._mover_for_object(highlighted_object)
        self._selected_objects = selected_objects
        self._movers: typing.List[empty_move.EmptyMove] = [
            self._mover_for_object(details) for details in self._selected_objects
        ]
        self._direction = self._highlighted_mover.get_move_direction()
        self._snapper = snapper
        self._all_sectors = all_sectors

    def end_move(self):
        for selected in self._selected_objects:
            if isinstance(selected.map_object, map_objects.EditorWall):
                previous_wall = selected.map_object.wall_previous_point
                if previous_wall.line_segment.is_empty:
                    operations.wall_delete.WallDelete(previous_wall).delete()

                next_wall = selected.map_object.wall_point_2
                if next_wall.line_segment.is_empty:
                    operations.wall_delete.WallDelete(next_wall).delete()
            
            elif isinstance(selected.map_object, map_objects.EditorSprite):
                operations.sprite_find_sector.SpriteFindSector(
                    selected.map_object,
                    self._all_sectors
                ).update_sector()

        for selected in self._selected_objects:
            if isinstance(selected.map_object, map_objects.EditorWall):
                operations.wall_link.SectorWallLink(
                    selected.map_object,
                    self._all_sectors
                ).try_link_wall()

    def move(self, delta: core.Vec3):
        self._do_move(self._direction * self._direction.dot(delta))

    def move_modified(self, delta: core.Vec3):
        self._do_move(core.Vec3(delta.x, delta.y, 0))

    def _do_move(self, delta: core.Vec3):
        for mover in self._movers:
            mover.move(delta, self._snapper)

    def _mover_for_object(self, details: highlighter.HighlightDetails):
        if isinstance(details.map_object, map_objects.wall.EditorWall):
            return wall_move.WallMove(details.map_object, details.part)

        if isinstance(details.map_object, map_objects.sector.EditorSector):
            return sector_move.SectorMove(details.map_object, details.part)

        if isinstance(details.map_object, map_objects.sprite.EditorSprite):
            return sprite_move.SpriteMove(details.map_object)

        raise NotImplementedError()
