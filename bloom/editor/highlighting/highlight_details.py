# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects


class HighlightDetails(typing.NamedTuple):
    map_object: typing.Union[
        map_objects.EmptyObject,
        map_objects.EditorWall,
        map_objects.EditorSector,
        map_objects.EditorSprite
    ]
    part: str
    hit_position: core.Vec3

    @property
    def is_sector(self):
        return isinstance(self.map_object, map_objects.EditorSector)

    @property
    def is_floor(self):
        return self.is_sector and self.part == map_objects.EditorSector.FLOOR_PART

    @property
    def is_ceiling(self):
        return self.is_sector and self.part == map_objects.EditorSector.FLOOR_PART

    @property
    def is_wall(self):
        return isinstance(self.map_object, map_objects.EditorWall)

    @property
    def is_sprite(self):
        return isinstance(self.map_object, map_objects.EditorSprite)

    def get_sector(self):
        return self.map_object.get_sector()