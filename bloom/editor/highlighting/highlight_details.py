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
