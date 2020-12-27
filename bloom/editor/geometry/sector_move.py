# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import grid_snapper, map_objects
from . import empty_move


class SpriteMove(typing.NamedTuple):
    start_position: core.Point2
    sprite: map_objects.EditorSprite

class SectorMove(empty_move.EmptyMove):

    def __init__(self, sector: map_objects.EditorSector, part: str, move_sprites_on_sectors: bool):
        self._sector = sector
        self._part = part

        if self._part == map_objects.EditorSector.FLOOR_PART:
            self._start_z = self._sector.floor_z
        else:
            self._start_z = self._sector.ceiling_z

        self._sprite_moves: typing.List[SpriteMove] = []
        if move_sprites_on_sectors:
            for sprite in self._sector.sprites:
                if self._sprite_should_move(sprite):
                    self._sprite_moves.append(
                        SpriteMove(
                            sprite.origin,
                            sprite
                        )
                    )

    def _sprite_should_move(self, sprite: map_objects.EditorSprite):
        origin = sprite.origin_2d
        return (self._part == map_objects.EditorSector.FLOOR_PART and \
                sprite.z_at_bottom >= self._sector.floor_z_at_point(origin)) or \
                (self._part == map_objects.EditorSector.CEILING_PART and \
                sprite.z_at_top <= self._sector.ceiling_z_at_point(origin))

    def get_move_direction(self) -> core.Vec3:
        return core.Vec3(0, 0, -1)

    def move(self, move_delta: core.Vec3, snapper: grid_snapper.GridSnapper):
        new_z = self._start_z + move_delta.z
        new_z = snapper.snap_to_grid(new_z)
        if self._part == map_objects.EditorSector.FLOOR_PART:
            self._sector.move_floor_to(new_z)
        else:
            self._sector.move_ceiling_to(new_z)

        snapped_delta_z = new_z - self._start_z
        sprite_delta = core.Vec3(0, 0, snapped_delta_z)
        for sprite_move in self._sprite_moves:
            sprite_move.sprite.move_to(
                sprite_move.start_position + sprite_delta
            )
