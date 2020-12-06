# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


from panda3d import core

from ... import editor, map_data
from .. import map_objects


class IncrementPanning:

    def __init__(self, map_object: map_objects.EmptyObject, part: str):
        self._map_object = map_object
        self._part = part

    def increment(self, amount: core.Vec2):
        from . import increment_repeats

        self._map_object.invalidate_geometry()

        if isinstance(self._map_object, map_objects.EditorWall):
            wall: map_data.wall.BuildWall = self._map_object.blood_wall.wall
            wall.panning_x = editor.to_build_panning_x(
                self._map_object.x_panning + amount.x
            )
            wall.panning_y = editor.to_build_panning_y(
                self._map_object.y_panning + amount.y
            )
        elif isinstance(self._map_object, map_objects.EditorSector):
            amount *= 16

            sector: map_data.sector.BuildSector = self._map_object.sector.sector
            if self._part == map_objects.EditorSector.FLOOR_PART:
                sector.floor_xpanning = editor.to_build_panning_x(
                    self._map_object.floor_x_panning + amount.x
                )
                sector.floor_ypanning = editor.to_build_panning_y(
                    self._map_object.floor_y_panning + amount.y
                )
            else:
                sector.ceiling_xpanning = editor.to_build_panning_x(
                    self._map_object.ceiling_x_panning + amount.x
                )
                sector.ceiling_ypanning = editor.to_build_panning_y(
                    self._map_object.ceiling_y_panning + amount.y
                )
        elif isinstance(self._map_object, map_objects.EditorSprite):
            increment_repeats.IncrementRepeats(
                self._map_object,
                self._part
            ).increment(amount)
