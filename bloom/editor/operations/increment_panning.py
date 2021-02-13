# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


from panda3d import core

from ... import cameras, editor, map_data
from .. import map_objects


class IncrementPanning:
    def __init__(
        self,
        camera_collection: cameras.Cameras,
        map_object: map_objects.EmptyObject,
        part: str,
    ):
        self._camera_collection = camera_collection
        self._map_object = map_object
        self._part = part

    def increment(self, amount: core.Vec2):
        from . import increment_repeats

        with self._map_object.undos.multi_step_undo("Increment Panning"):
            with self._map_object.change_blood_object():
                if isinstance(self._map_object, map_objects.EditorWall):
                    wall: map_data.wall.BuildWall = self._map_object.blood_wall.wall
                    wall.panning_x = editor.to_build_panning_x(
                        self._map_object.x_panning + amount.x
                    )
                    wall.panning_y = editor.to_build_panning_y(
                        self._map_object.y_panning + amount.y
                    )
                    message = f"Wall Panning: ({wall.panning_x}, {wall.panning_y})"
                    self._camera_collection.set_info_text(message)
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
                        message = f"Sector Floor Panning: ({sector.floor_xpanning}, {sector.floor_ypanning})"
                    else:
                        sector.ceiling_xpanning = editor.to_build_panning_x(
                            self._map_object.ceiling_x_panning + amount.x
                        )
                        sector.ceiling_ypanning = editor.to_build_panning_y(
                            self._map_object.ceiling_y_panning + amount.y
                        )
                        message = f"Sector Ceiling Panning: ({sector.ceiling_xpanning}, {sector.ceiling_ypanning})"
                    self._camera_collection.set_info_text(message)
                elif isinstance(self._map_object, map_objects.EditorSprite):
                    increment_repeats.IncrementRepeats(
                        self._camera_collection, self._map_object, self._part
                    ).increment(amount)
