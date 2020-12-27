# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import grid_snapper, highlighter, map_objects, operations
from ..highlighting import highlight_details
from . import (empty_move, sector_move, sector_move_walls, sprite_move,
               wall_move)


class Move:

    def __init__(
        self,
        selected_objects: typing.List[highlight_details.HighlightDetails],
        highlighted_object: highlight_details.HighlightDetails,
        snapper: grid_snapper.GridSnapper,
        all_sectors: map_objects.SectorCollection,
        move_sprites_on_sectors: bool,
        move_sector_walls: bool
    ):
        self._hit = highlighted_object.hit_position
        self._move_sector_walls = move_sector_walls
        self._move_sprites_on_sectors = move_sprites_on_sectors
        self._highlighted_mover = self._mover_for_object(highlighted_object)
        self._selected_objects = selected_objects
        self._movers: typing.List[empty_move.EmptyMove] = [
            self._mover_for_object(details) for details in self._selected_objects
        ]
        self._direction = self._highlighted_mover.get_move_direction()
        self._snapper = snapper
        self._all_sectors = all_sectors

    def end_move(self):
        ajusted_sector_shapes: typing.Set[map_objects.EditorSector] = set()
        for selected in self._selected_objects:
            if isinstance(selected.map_object, map_objects.EditorWall):
                ajusted_sector_shapes.add(selected.map_object.sector)
                if selected.map_object.other_side_sector is not None:
                    ajusted_sector_shapes.add(selected.map_object.other_side_sector)

                previous_wall = selected.map_object.wall_previous_point
                if previous_wall.line_segment.is_empty:
                    operations.wall_delete.WallDelete(previous_wall).delete()

                next_wall = selected.map_object.wall_point_2
                if next_wall.line_segment.is_empty:
                    operations.wall_delete.WallDelete(next_wall).delete()

                if previous_wall.other_side_wall is not None:
                    wall: map_objects.EditorWall = previous_wall.other_side_wall.wall_previous_point
                    if wall.line_segment.is_empty:
                        operations.wall_delete.WallDelete(wall).delete()

            elif isinstance(selected.map_object, map_objects.EditorSprite):
                operations.sprite_find_sector.SpriteFindSector(
                    selected.map_object,
                    self._all_sectors.sectors
                ).update_sector()

        for editor_sector in ajusted_sector_shapes:
            for sprite in editor_sector.sprites:
                operations.sprite_find_sector.SpriteFindSector(
                    sprite,
                    self._all_sectors.sectors
                ).update_sector()

        for selected in self._selected_objects:
            if isinstance(selected.map_object, map_objects.EditorWall):
                operations.wall_link.SectorWallLink(
                    selected.map_object,
                    self._all_sectors
                ).try_link_wall()
                operations.wall_link.SectorWallLink(
                    selected.map_object.wall_previous_point,
                    self._all_sectors
                ).try_link_wall()

    def move(self, delta: core.Vec3):
        if self._direction is None:
            self.move_modified(delta)
        else:
            self._do_move(self._direction * self._direction.dot(delta))

    def move_modified(self, delta: core.Vec3):
        self._do_move(core.Vec3(delta.x, delta.y, 0))

    def _do_move(self, delta: core.Vec3):
        for mover in self._movers:
            mover.move(delta, self._snapper)

    def _mover_for_object(self, details: highlight_details.HighlightDetails):
        if self._move_sector_walls:
            if not isinstance(details.map_object, map_objects.EditorSector):
                raise ValueError('Invalid map object for sector wall move')
            return sector_move_walls.SectorMoveWalls(details.map_object)

        if isinstance(details.map_object, map_objects.EditorWall):
            return wall_move.WallMove(details.map_object, details.part)

        if isinstance(details.map_object, map_objects.EditorSector):
            return sector_move.SectorMove(details.map_object, details.part, self._move_sprites_on_sectors)

        if isinstance(details.map_object, map_objects.EditorSprite) or \
                isinstance(details.map_object, map_objects.EditorMarker):
            return sprite_move.SpriteMove(details.map_object)

        raise NotImplementedError()
