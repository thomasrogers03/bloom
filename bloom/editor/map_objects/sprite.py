# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import bullet, core

from ... import constants, editor, game_map, map_data
from ...tiles import manager
from .. import plane, sector_geometry, segment
from . import empty_object, sprite_highlight


class EditorSprite(empty_object.EmptyObject):
    PART_NAME = 'sprite'

    def __init__(
        self,
        sprite: map_data.sprite.Sprite,
        name: str,
        sector: 'bloom.editor.map_objects.sector.EditorSector',
        tile_manager: manager.Manager
    ):
        self._sector = sector
        self._name = name
        self._sprite = sprite
        self._tile_manager = tile_manager
        self._sprite_collision: core.NodePath = None
        self._targets = []

    def move_to_sector(self, new_sector: 'bloom.editor.map_objects.sector.EditorSector'):
        self._sector = new_sector
        self.invalidate_geometry()

    def get_geometry_part(self, part: str) -> core.NodePath:
        return self._sector.get_geometry_part(part)

    def show_highlight(self, part: str, rgb_colour: core.Vec3):
        display = self.get_geometry_part(part)
        if display is not None and not display.is_empty():
            display.set_color(
                rgb_colour.x * self.shade,
                rgb_colour.y * self.shade,
                rgb_colour.z * self.shade,
                1
            )

    def hide_highlight(self, part: str):
        display = self.get_geometry_part(part)
        if display is not None and not display.is_empty():
            display.set_color(self.shade, self.shade, self.shade, 1)


    @property
    def targets(self):
        return self._targets

    @property
    def size(self):
        tile_dimensions = self._tile_manager.get_tile_dimensions(
            self._sprite.sprite.picnum
        )
        return core.Vec2(tile_dimensions.x * self.x_repeat, tile_dimensions.y * self.y_repeat)

    @property
    def position(self):
        return core.Point3(
            self._sprite.sprite.position_x,
            self._sprite.sprite.position_y,
            editor.to_height(self._sprite.sprite.position_z) - self._offsets.y,
        )

    @property
    def origin_2d(self):
        return self.position.xy

    @property
    def origin(self):
        return self.position

    @property
    def position_2d(self):
        return core.Point2(
            self._sprite.sprite.position_x,
            self._sprite.sprite.position_y
        )

    @property
    def theta(self):
        return editor.to_degrees(self._sprite.sprite.theta)

    @property
    def shade(self):
        sprite_shade = self.get_shade(None)
        return sprite_shade * self._sector.floor_shade

    def get_shade(self, part: str):
        return editor.to_shade(self._sprite.sprite.shade)

    def set_shade(self, part: str, value: float):
        self.invalidate_geometry()
        self._sprite.sprite.shade = editor.to_build_shade(value)

    def get_direction(self) -> core.Vec2:
        sin_theta = math.sin(math.radians(self.theta))
        cos_theta = math.cos(math.radians(self.theta))

        return core.Vec2(-sin_theta, cos_theta)

    def get_orthogonal(self) -> core.Vec2:
        direction = self.get_direction()
        return core.Vec2(direction.y, -direction.x)

    def get_normal(self) -> core.Vec2:
        return self.get_orthogonal().normalized()

    @property
    def rx_id(self):
        return self._sprite.data.rx_id

    @property
    def tx_id(self):
        return self._sprite.data.tx_id

    @property
    def x_repeat(self):
        return editor.to_sprite_repeat(self._sprite.sprite.repeat_x)

    @property
    def y_repeat(self):
        return editor.to_sprite_repeat(self._sprite.sprite.repeat_y)

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
    def segment(self):
        if self.is_directional:
            half_width = self.size.x / 2
            offset = self.get_normal() * half_width

            return segment.Segment(self.origin_2d - offset, self.origin_2d + offset)

    def set_repeats(self, x_repeat: float, y_repeat: float):
        self.invalidate_geometry()
        self._sprite.sprite.repeat_x = editor.to_build_sprite_repeat(x_repeat)
        self._sprite.sprite.repeat_y = editor.to_build_sprite_repeat(y_repeat)

    def get_type(self) -> int:
        return self._sprite.sprite.tags[0]

    def get_picnum(self, part: str):
        return self._sprite.sprite.picnum

    def set_picnum(self, picnum: int):
        self._sprite.sprite.picnum = picnum
        self.invalidate_geometry()

    def invalidate_geometry(self):
        self._sector.invalidate_geometry()

    def get_part_at_point(self, point: core.Point3):
        if self.is_facing or self.is_directional:
            if self.is_directional:
                if not self.segment.point_on_line(point.xy):
                    return None

            half_height = self.size.y / 2
            if point.z <= self.position.z + half_height and \
                    point.z >= self.position.z - half_height:
                return self._name
            return None

        relative_point = point - self.position
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

    def intersect_line(self, point: core.Point3, direction: core.Vec3) -> core.Point2:
        if self.is_facing:
            direction_2d = core.Vec2(direction.x, direction.y)

            orthogonal = core.Vec2(direction_2d.y, -direction_2d.x)
            orthogonal.normalize()

            half_width = self.size.x / 2
            orthogonal *= half_width

            return segment.Segment(
                self.position_2d + orthogonal,
                self.position_2d - orthogonal
            ).intersect_line(point.xy, direction_2d)
        elif self.is_floor:
            sprite_position = self.position
            sprite_direction = self.get_direction()
            sprite_plane = plane.Plane(
                sprite_position,
                core.Point3(
                    sprite_position.x + 1,
                    sprite_position.y,
                    sprite_position.z),
                core.Point3(
                    sprite_position.x,
                    sprite_position.y + 1,
                    sprite_position.z
                ),
            )
            intersection = sprite_plane.intersect_line(point, direction)
            if intersection is not None:
                return intersection.xy
        else:
            sprite_position = self.position
            sprite_direction = self.get_orthogonal()
            sprite_plane = plane.Plane(
                sprite_position,
                core.Point3(
                    sprite_position.x + sprite_direction.x,
                    sprite_position.y + sprite_direction.y,
                    sprite_position.z
                ),
                core.Point3(
                    sprite_position.x,
                    sprite_position.y,
                    sprite_position.z - 1
                )
            )
            intersection = sprite_plane.intersect_line(point, direction)
            if intersection is not None:
                return intersection.xy

    @property
    def is_facing(self):
        return self._sprite.sprite.stat.facing == 0

    @property
    def is_directional(self):
        return self._sprite.sprite.stat.facing == 1

    @property
    def is_floor(self):
        return self._sprite.sprite.stat.facing == 2

    def setup(self, targets: list):
        self._targets = targets

    def setup_geometry(self, all_geometry: sector_geometry.SectorGeometry):
        texture_size = all_geometry.get_tile_dimensions(self._sprite.sprite.picnum)

        if self.is_facing:
            sprite_collision = all_geometry.sprite_geometry.add_facing_sprite(
                self._name,
                {'sprite': self},
                self._sprite.sprite.picnum,
                self._sprite.sprite.palette,
                self._sprite.sprite.stat.centring,
                self._sprite.sprite.stat.one_sided,
                self.theta
            )
        elif self.is_floor:
            sprite_collision = all_geometry.sprite_geometry.add_floor_sprite(
                self._name,
                {'sprite': self},
                self._sprite.sprite.picnum,
                self._sprite.sprite.palette,
                self._sprite.sprite.stat.centring,
                self._sprite.sprite.stat.one_sided,
                self.theta
            )
        else:
            sprite_collision = all_geometry.sprite_geometry.add_directional_sprite(
                self._name,
                {'sprite': self},
                self._sprite.sprite.picnum,
                self._sprite.sprite.palette,
                self._sprite.sprite.stat.centring,
                self._sprite.sprite.stat.one_sided,
                self.theta
            )

        sprite_collision.set_pos(self.position)
        if self.is_floor:
            y_scale = texture_size.y * self.y_repeat
            z_scale = texture_size.x * self.x_repeat
        else:
            y_scale = texture_size.x * self.x_repeat
            z_scale = texture_size.y * self.y_repeat

        sprite_collision.set_scale(
            texture_size.x * self.x_repeat,
            y_scale,
            z_scale,
        )
        sprite_collision.set_color(self.shade, self.shade, self.shade, 1)

        texture_scale = core.Vec2(-1, 1)
        if self._sprite.sprite.stat.xflip:
            texture_scale.x = 1
        if self._sprite.sprite.stat.yflip:
            texture_scale.y = -1
        sprite_collision.set_tex_scale(
            core.TextureStage.get_default(),
            texture_scale
        )

        self._sprite_collision = sprite_collision
        self._needs_geometry_reset = False

    def move_to(self, position: core.Point3):
        if self._sprite_collision is not None:
            self._sprite_collision.set_pos(position)
        self._sprite.sprite.position_x = int(position.x)
        self._sprite.sprite.position_y = int(position.y)
        self._sprite.sprite.position_z = editor.to_build_height(
            position.z + self._offsets.y
        )

    def prepare_to_persist(
        self,
        find_sector: typing.Callable[['editor.sector.EditorSector', core.Point3], 'editor.sector.EditorSector'],
        sector_mapping: typing.Dict['editor.sector.EditorSector', int]
    ) -> map_data.sprite.Sprite:
        sector = find_sector(self._sector, self.position)
        if sector is not None:
            self._sprite.sprite.sector_index = sector_mapping[sector]
        else:
            self._sprite.sprite.sector_index = -1

        return self._sprite

    @property
    def _offsets(self):
        tile_offsets = self._tile_manager.get_tile_offsets(
            self._sprite.sprite.picnum
        )
        return core.Vec2(tile_offsets.x * self.x_repeat, tile_offsets.y * self.y_repeat)

    def _get_highlighter(self):
        return sprite_highlight
