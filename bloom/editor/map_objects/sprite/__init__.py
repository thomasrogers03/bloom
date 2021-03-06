# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import bullet, core

from .... import audio, constants, editor, game_map, map_data, seq
from ....tiles import manager
from ... import (
    event_grouping,
    marker_constants,
    plane,
    sector_geometry,
    segment,
    undo_stack,
)
from .. import empty_object, sprite_highlight
from . import sprite_constants
from . import type_descriptor as sprite_type_descriptor


class EditorSprite(empty_object.EmptyObject):
    PART_NAME = "sprite"
    _AMBIENT_SFX_TYPE = 710
    _SOUND_DISTANCE_SCALE = 20
    _STATE_OFF = 0
    _STATE_ON = 1

    def __init__(
        self,
        sprite: map_data.sprite.Sprite,
        name: str,
        sector: typing.Any,
        audio_manager: audio.Manager,
        tile_manager: manager.Manager,
        seq_manager: seq.Manager,
        undos: undo_stack.UndoStack,
    ):
        super().__init__(undos)

        self._sector = sector
        self._name = name
        self._sprite = sprite
        self._audio_manager = audio_manager
        self._tile_manager = tile_manager
        self._seq_manager = seq_manager
        self._sprite_collision: core.NodePath = None

    def move_to_sector(self, new_sector: typing.Any):
        self._sector = new_sector
        self.invalidate_geometry()

    def get_geometry_part(self, part: str) -> core.NodePath:
        return self._sector.get_geometry_part(part)

    def get_data(self):
        return self._sprite.data

    def get_stat_for_part(self, part: str):
        return self._sprite.sprite.stat

    @property
    def type_descriptor(self):
        return sprite_constants.sprite_types[self._type_number]

    @type_descriptor.setter
    def type_descriptor(self, value: sprite_type_descriptor.Descriptor):
        self._type_number = value.sprite_type

    @property
    def _type_number(self):
        return self._sprite.sprite.tags[0]

    @_type_number.setter
    def _type_number(self, value: int):
        self._sprite.sprite.tags[0] = value

    @property
    def size(self):
        return self._size_for_tile(self.get_picnum(None))

    @property
    def position(self):
        return self.origin

    @property
    def _z(self):
        return editor.to_height(self._sprite.sprite.position_z) - self._offsets.y

    def _set_z(self, value: float):
        if self._sprite_collision is not None:
            self._sprite_collision.set_z(value)
        self._sprite.sprite.position_z = editor.to_build_height(value + self._offsets.y)

    @property
    def z_at_bottom(self):
        return self._z + self.size.y / 2

    def set_z_at_bottom(self, value: float):
        self._set_z(value - self.size.y / 2)

    @property
    def z_at_top(self):
        return self.z_at_bottom - self.size.y

    def set_z_at_top(self, value: float):
        self.set_z_at_bottom(value + self.size.y)

    @property
    def origin_2d(self):
        return core.Point2(
            self._sprite.sprite.position_x,
            self._sprite.sprite.position_y,
        )

    @property
    def origin(self):
        return core.Point3(self.origin_2d.x, self.origin_2d.y, self._z)

    @property
    def position_2d(self):
        return core.Point2(
            self._sprite.sprite.position_x, self._sprite.sprite.position_y
        )

    @property
    def theta(self):
        return editor.to_degrees(self._sprite.sprite.theta)

    def set_theta(self, value: float):
        self.invalidate_geometry()
        self._sprite.sprite.theta = editor.to_build_angle(value)

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

    def set_sector(self, value, new_name: str):
        self._sector = value
        self._name = new_name
        self.invalidate_geometry()

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
        return None

    def set_repeats(self, x_repeat: float, y_repeat: float):
        self.invalidate_geometry()
        self._sprite.sprite.repeat_x = editor.to_build_sprite_repeat(x_repeat)
        self._sprite.sprite.repeat_y = editor.to_build_sprite_repeat(y_repeat)

    def get_picnum(self, part: typing.Optional[str]):
        return self._sprite.sprite.picnum

    def set_picnum(self, part: typing.Optional[str], picnum: int):
        self._sprite.sprite.picnum = picnum
        self.invalidate_geometry()

    def invalidate_geometry(self):
        self._sector.invalidate_geometry()

    @property
    def default_part(self):
        return self._name

    def get_part_at_point(self, point: core.Point3):
        if self.is_facing or self.is_directional:
            if self.is_directional:
                if not self.segment.point_on_line(point.xy):
                    return None

            if point.z <= self.z_at_bottom and point.z >= self.z_at_top:
                return self._name
            return None

        relative_point = point - self.position
        theta_radians = math.radians(self.theta)
        relative_point = core.Point3(
            math.cos(theta_radians) * relative_point.x
            - math.sin(theta_radians) * relative_point.y,
            math.sin(theta_radians) * relative_point.x
            + math.cos(theta_radians) * relative_point.y,
            relative_point.z,
        )
        half_size = self.size / 2
        if (
            relative_point.x >= -half_size.x
            and relative_point.x <= half_size.x
            and relative_point.y >= -half_size.y
            and relative_point.y <= half_size.y
            and round(relative_point.z) == 0
        ):
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
                self.position_2d + orthogonal, self.position_2d - orthogonal
            ).intersect_line(point.xy, direction_2d)
        elif self.is_floor:
            sprite_position = self.position
            sprite_direction = self.get_direction()
            sprite_plane = plane.Plane(
                sprite_position,
                core.Point3(
                    sprite_position.x + 1, sprite_position.y, sprite_position.z
                ),
                core.Point3(
                    sprite_position.x, sprite_position.y + 1, sprite_position.z
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
                    sprite_position.z,
                ),
                core.Point3(
                    sprite_position.x, sprite_position.y, sprite_position.z - 1
                ),
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

    def setup_geometry(self, all_geometry: sector_geometry.SectorGeometry):
        picnum = self.get_picnum(None)

        if self.is_facing:
            sprite_create = all_geometry.sprite_geometry.add_facing_sprite
        elif self.is_floor:
            sprite_create = all_geometry.sprite_geometry.add_floor_sprite
        else:
            sprite_create = all_geometry.sprite_geometry.add_directional_sprite
        sprite_collision = sprite_create(
            self._name,
            {"sprite": self},
            picnum,
            self._sprite.sprite.palette,
            self._sprite.sprite.stat.blocking
            | (self._sprite.sprite.stat.blocking2 << 1),
            self._sprite.sprite.stat.centring,
            self._sprite.sprite.stat.one_sided,
            self.theta,
        )

        self._sprite_collision = sprite_collision
        self._sprite_collision.set_pos(self.position)
        self._set_display_size(self.get_picnum(None))

        alpha = 1.0
        if self._sprite.sprite.stat.translucent_rev:
            alpha = 0.75
        elif self._sprite.sprite.stat.translucent:
            alpha = 0.5
        shade = self._shade_to_colour_channel(self.shade)
        self._sprite_collision.set_color(shade, shade, shade, alpha)

        self.update_ambient_sound()
        self._needs_geometry_reset = False

    def update(self, ticks: int, art_manager: manager.Manager):
        node_path: core.NodePath = self._sprite_collision.find("**/geometry")
        if node_path.is_empty():
            return

        animation_data_and_lookup = node_path.get_python_tag("animation_data")
        if self._seq is not None:
            frame_index = (
                int((4 * ticks) / self._seq.header.ticks_per_frame)
                % self._seq.header.frame_count
            )
            frame = self._seq.frames[frame_index]

            self._set_display_size(frame.stat.tile)
            node_path.set_texture(art_manager.get_tile(frame.stat.tile, frame.palette))

        elif animation_data_and_lookup is not None:
            animation_data: manager.AnimationData = animation_data_and_lookup[0]
            lookup: int = animation_data_and_lookup[1]
            offset = (
                ticks // animation_data.ticks_per_frame
            ) % animation_data.animation_count
            new_picnum = animation_data.picnum + offset

            self._set_display_size(new_picnum)
            node_path.set_texture(art_manager.get_tile(new_picnum, lookup))

    def update_ambient_sound(self):
        if (
            self._sprite.sprite.tags[0] != self._AMBIENT_SFX_TYPE
            or self._sprite.data.state != self._STATE_ON
            or self._sprite_collision is None
        ):
            return

        attachment = audio.manager.SoundAttachment(
            self._sprite.data.data3,
            self._sprite_collision,
            self._sprite.data.data1 * self._SOUND_DISTANCE_SCALE,
            self._sprite.data.data2 * self._SOUND_DISTANCE_SCALE,
            self._sprite.data.data4 / 100,
        )

        self._audio_manager.attach_sound_to_object(attachment)

    def move_to(self, position: core.Point3):
        if self._sprite_collision is not None:
            self._sprite_collision.set_pos(position)
        self._sprite.sprite.position_x = int(position.x)
        self._sprite.sprite.position_y = int(position.y)
        self._set_z(position.z)

    def prepare_to_persist(
        self, sector_mapping: typing.Dict[typing.Any, int]
    ) -> map_data.sprite.Sprite:
        self._sprite.sprite.sector_index = sector_mapping[self._sector]
        self._sprite.sprite.owner = -1
        return self._sprite

    def _size_for_tile(self, tile: int):
        tile_dimensions = self._tile_manager.get_tile_dimensions(tile)
        return core.Vec2(
            tile_dimensions.x * self.x_repeat, tile_dimensions.y * self.y_repeat
        )

    def _set_display_size(self, tile: int):
        sprite_size = self._size_for_tile(tile)
        if self.is_floor:
            y_scale = sprite_size.y
            z_scale = sprite_size.x
        else:
            y_scale = sprite_size.x
            z_scale = sprite_size.y

        self._sprite_collision.set_scale(sprite_size.x, y_scale, z_scale)

        texture_scale = core.Vec2(-1, 1)
        if self._sprite.sprite.stat.xflip:
            texture_scale.x = 1
        if self._sprite.sprite.stat.yflip:
            texture_scale.y = -1
        self._sprite_collision.set_tex_scale(
            core.TextureStage.get_default(), texture_scale
        )

    @property
    def _blood_object(self):
        return self._sprite

    @_blood_object.setter
    def _blood_object(self, value):
        self._sprite = value

    @property
    def _seq(self):
        seq_number = self.type_descriptor.seq
        return self._seq_manager.get_seq(seq_number)

    @property
    def _offsets(self):
        tile_offsets = self._tile_manager.get_tile_offsets(self._sprite.sprite.picnum)
        return core.Vec2(tile_offsets.x * self.x_repeat, tile_offsets.y * self.y_repeat)

    def _get_highlighter(self):
        return sprite_highlight
