# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


from panda3d import core

from ... import editor, map_data
from .. import map_objects


class IncrementRepeats:

    def __init__(self, map_object: map_objects.EmptyObject, part: str):
        self._map_object = map_object
        self._part = part

    def increment(self, amount: core.Vec2):
        from . import increment_panning

        with self._map_object.undos.multi_step_undo('Increment Repeats'):
            with self._map_object.change_blood_object():
                if isinstance(self._map_object, map_objects.EditorWall):
                    wall: map_data.wall.BuildWall = self._map_object.blood_wall.wall

                    wall.repeat_x = editor.to_build_repeat_x(
                        self._map_object.x_repeat + amount.x * 8
                    )
                    wall.repeat_y = editor.to_build_repeat_y(
                        self._map_object.y_repeat + amount.y / 64
                    )
                elif isinstance(self._map_object, map_objects.EditorSector):
                    increment_panning.IncrementPanning(
                        self._map_object,
                        self._part
                    ).increment(amount)
                elif isinstance(self._map_object, map_objects.EditorSprite):
                    sprite: map_data.sprite.BuildSprite = self._map_object.sprite.sprite

                    sprite.repeat_x = editor.to_build_sprite_repeat(
                        self._map_object.x_repeat + amount.x
                    )
                    sprite.repeat_y = editor.to_build_sprite_repeat(
                        self._map_object.y_repeat + amount.y
                    )
