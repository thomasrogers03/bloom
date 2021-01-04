# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import core

from ... import editor, map_data
from ...utils import shapes
from .. import marker_constants, plane, sector_geometry, undo_stack
from . import empty_object, marker_highlight


class EditorMarker(empty_object.EmptyObject):
    _RADIUS = 64

    def __init__(
        self,
        sprite: map_data.sprite.Sprite,
        name: str,
        sector: 'bloom.editor.map_objects.sector.EditorSector',
        undos: undo_stack.UndoStack
    ):
        super().__init__(undos)

        self._sprite = sprite
        self._name = name
        self._sector = sector
        self._display: core.NodePath = None
        self._needs_geometry_reset = False

        self._sprite.sprite.stat.invisible = 1

    @property
    def is_marker(self):
        return True

    @property
    def size(self):
        return core.Vec2(self._RADIUS, self._RADIUS) * 2

    @property
    def origin_2d(self):
        return core.Point2(
            self._sprite.sprite.position_x,
            self._sprite.sprite.position_y,
        )

    @property
    def origin(self):
        return core.Point3(
            self.origin_2d.x,
            self.origin_2d.y,
            self._z
        )

    @property
    def sector(self):
        return self._sector

    def get_sector(self):
        return self._sector

    @property
    def sprite(self):
        return self._sprite

    @property
    def is_geometry(self):
        return False

    @property
    def theta(self):
        return editor.to_degrees(self._sprite.sprite.theta)

    def set_theta(self, value: float):
        self.invalidate_geometry()
        self._sprite.sprite.theta = editor.to_build_angle(value)

    def get_geometry_part(self, part: str) -> core.NodePath:
        return self._sector.get_geometry_part(part)

    def get_direction(self) -> core.Vec2:
        sin_theta = math.sin(math.radians(self.theta))
        cos_theta = math.cos(math.radians(self.theta))

        return core.Vec2(-sin_theta, cos_theta)

    def get_part_at_point(self, point: core.Point3):
        relative_point = point - self.origin
        theta_radians = math.radians(self.theta)
        relative_point = core.Point3(
            math.cos(theta_radians) * relative_point.x -
            math.sin(theta_radians) * relative_point.y,
            math.sin(theta_radians) * relative_point.x +
            math.cos(theta_radians) * relative_point.y,
            relative_point.z
        )
        half_size = self.size / 2
        if relative_point.x >= -half_size.x and \
                relative_point.x <= half_size.x and \
                relative_point.y >= -half_size.y and \
                relative_point.y <= half_size.y and \
                round(relative_point.z) == 0:
            return self._name

        return None

    def invalidate_geometry(self):
        if not self._needs_geometry_reset:
            self._needs_geometry_reset = True
            self._clear_display()
            self._sector.invalidate_geometry()

    def intersect_line(self, point: core.Point3, direction: core.Vec3) -> core.Point2:
        sprite_position = self.origin
        sprite_plane = plane.Plane(
            sprite_position,
            core.Point3(
                sprite_position.x + 1,
                sprite_position.y,
                sprite_position.z
            ),
            core.Point3(
                sprite_position.x,
                sprite_position.y + 1,
                sprite_position.z
            ),
        )
        intersection = sprite_plane.intersect_line(point, direction)
        if intersection is not None:
            return intersection.xy

    def setup_geometry(self, all_geometry: sector_geometry.SectorGeometry):
        self._clear_display()
        self._display = shapes.make_circle(
            all_geometry.display,
            core.Point3(0, 0, 0),
            self._RADIUS,
            12
        )
        self._display.set_pos(self.origin)
        if self.get_type() == marker_constants.AXIS_MARKER_TAG:
            self._display.set_color(1, 0, 1, 0.5)
        else:
            self._display.set_color(0, 0, 1, 0.5)
        self._display.set_transparency(True)
        self._display.set_name(self._name)
        self._needs_geometry_reset = False

    def move_to(self, position: core.Point3):
        if self._display is not None:
            self._display.set_pos(position.x, position.y, self._z)
        self._sprite.sprite.position_x = int(position.x)
        self._sprite.sprite.position_y = int(position.y)

    def set_source_event_grouping(self, event_grouping):
        pass

    def set_target_event_grouping(self, event_grouping):
        pass

    def prepare_to_persist(
        self,
        sector_mapping: typing.Dict['editor.sector.EditorSector', int]
    ) -> map_data.sprite.Sprite:
        self._sprite.sprite.sector_index = sector_mapping[self._sector]
        self._sprite.sprite.owner = sector_mapping[self._sector]
        return self._sprite

    def get_type(self):
        return self._sprite.sprite.tags[0]

    @property
    def _blood_object(self):
        return self._sprite

    @_blood_object.setter
    def _blood_object(self, value):
        self._sprite = value

    @property
    def _z(self):
        return self._sector.floor_z_at_point(self.origin_2d) - 64

    def _clear_display(self):
        if self._display is not None:
            self._display.remove_node()
            self._display = None

    def _get_highlighter(self):
        return marker_highlight
