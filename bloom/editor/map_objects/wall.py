# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import bullet, core

from ... import constants, editor, game_map, map_data
from .. import sector_geometry, segment
from . import empty_object, geometry_highlight


class EditorWall(empty_object.EmptyObject):
    _MASK_WALL_PART = 'middle_highlight'
    _LENGTH_REPEAT_SCALE = 1 / 16.0

    def __init__(
        self,
        blood_wall: map_data.wall.Wall,
        name: str,
        editor_sector
    ):
        self._sector = editor_sector
        self._name = name
        self._wall = blood_wall
        self.wall_previous_point: EditorWall = None
        self._wall_point_2: EditorWall = None
        self._other_side_wall: EditorWall = None
        self._targets = []
        self._debug_display: core.NodePath = None
        self._needs_geometry_reset = False
        self._is_other_side_sector_visible: bool = None
        self._is_destroyed = False

    def setup(
        self,
        wall_point_2: 'EditorWall',
        other_side_wall: 'EditorWall',
        targets: list
    ):
        self._wall_point_2 = wall_point_2
        self._other_side_wall = other_side_wall
        self._targets = targets

    def link(self, otherside_wall: 'EditorWall'):
        if self._other_side_wall is not None:
            message = 'Tried to link to a wall when we are already linking to one'
            raise AssertionError(message)

        self.invalidate_geometry()
        self._other_side_wall = otherside_wall
        otherside_wall._other_side_wall = self

    def unlink(self):
        self.invalidate_geometry()
        other_side_wall = self._other_side_wall
        self._other_side_wall = None
        if other_side_wall is not None:
            other_side_wall.unlink()

    def all_walls_at_point_1(self):
        result: typing.Set[EditorWall] = set()
        self._gather_walls_at_point_1(result)
        return list(result)

    def iterate_wall_bunch(self) -> typing.Iterable:
        yield self
        current_wall = self.wall_point_2
        while current_wall != self:
            yield current_wall
            current_wall = current_wall.wall_point_2

    def _gather_walls_at_point_1(self, seen: typing.Set['EditorWall']):
        if self in seen:
            return

        seen.add(self)

        if self.other_side_wall is not None:
            self.other_side_wall.wall_point_2._gather_walls_at_point_1(seen)

        if self.wall_previous_point.other_side_wall is not None:
            self.wall_previous_point.other_side_wall._gather_walls_at_point_1(seen)

    def setup_geometry(self, all_geometry: sector_geometry.SectorGeometry):
        debug_display_node = core.TextNode('debug')
        text = f'Angle: {self.get_direction_theta()}\n'
        text += f'Direction: {self.get_direction()}\n'
        text += f'Length: {self.get_direction().length()}'
        debug_display_node.set_text(text)
        debug_display_node.set_align(core.TextNode.A_center)
        self._debug_display = all_geometry.scene.attach_new_node(debug_display_node)
        self._debug_display.set_pos(self.get_centre())
        self._debug_display.set_billboard_axis()
        self._debug_display.set_scale(-96)
        self._debug_display.hide()

        if self._wall.wall.stat.poly_blue:
            colour = core.Vec4(0, 0, 1, 1)
        elif self._wall.wall.stat.poly_green:
            colour = core.Vec4(0, 1, 0, 1)
        elif self._other_side_wall is None:
            colour = core.Vec4(1, 1, 1, 1)
        else:
            colour = core.Vec4(1, 0, 0, 1)
        all_geometry.add_2d_geometry(self.point_1, self.point_2, colour)

        if self._other_side_wall is None:
            self._make_wall_part(
                all_geometry,
                'full',
                self._sector.floor_z,
                self._sector.ceiling_z,
                lambda point: self._sector.floor_z_at_point(point),
                lambda point: self._sector.ceiling_z_at_point(point),
                self._wall.wall.picnum
            )
        else:
            if not self.other_side_sector.sector.sector.floor_stat.parallax:
                self._make_wall_part(
                    all_geometry,
                    'lower',
                    self._sector.floor_z,
                    self.other_side_sector.floor_z,
                    lambda point: self._sector.floor_z_at_point(point),
                    lambda point: self.other_side_sector.floor_z_at_point(point),
                    self._wall.wall.picnum
                )
            if not self.other_side_sector.sector.sector.ceiling_stat.parallax:
                self._make_wall_part(
                    all_geometry,
                    'upper',
                    self.other_side_sector.ceiling_z,
                    self._sector.ceiling_z,
                    lambda point: self.other_side_sector.ceiling_z_at_point(point),
                    lambda point: self._sector.ceiling_z_at_point(point),
                    self._wall.wall.picnum
                )
            if self._wall.wall.stat.masking > 0 and self._wall.wall.over_picnum > 0:
                self._make_wall_part(
                    all_geometry,
                    self._MASK_WALL_PART,
                    self.other_side_sector.floor_z,
                    self.other_side_sector.ceiling_z,
                    lambda point: self.other_side_sector.floor_z_at_point(point),
                    lambda point: self.other_side_sector.ceiling_z_at_point(point),
                    self._wall.wall.over_picnum
                )

        self._needs_geometry_reset = False

    def get_geometry_part(self, part: str) -> core.NodePath:
        return self._sector.get_geometry_part(part)

    def is_other_side_sector_visible(self):
        if self._other_side_wall is None:
            return False

        if self._is_other_side_sector_visible is not None:
            return self._is_other_side_sector_visible

        middle_bottom = max(
            self.other_side_sector.floor_z_at_point(self.point_1),
            self.other_side_sector.floor_z_at_point(self.point_2),
        )
        middle_top = min(
            self.other_side_sector.ceiling_z_at_point(self.point_1),
            self.other_side_sector.ceiling_z_at_point(self.point_2),
        )
        if middle_top >= middle_bottom:
            self._is_other_side_sector_visible = False
            return False

        lower_bottom = max(
            self._sector.floor_z_at_point(self.point_1),
            self._sector.floor_z_at_point(self.point_2),
        )
        if lower_bottom <= middle_top:
            self._is_other_side_sector_visible = False
            return False

        upper_top = max(
            self._sector.ceiling_z_at_point(self.point_1),
            self._sector.ceiling_z_at_point(self.point_2),
        )
        if upper_top >= middle_bottom:
            self._is_other_side_sector_visible = False
            return False

        self._is_other_side_sector_visible = True
        return True

    def invalidate_geometry(self):
        if not self._needs_geometry_reset:
            if self._debug_display is not None:
                self._debug_display.remove_node()
                self._debug_display = None
            self._needs_geometry_reset = True
            self._sector.invalidate_geometry()

    def teleport_point_1_to(self, position: core.Point2):
        self.invalidate_geometry()

        self._wall.wall.position_x = int(position.x)
        self._wall.wall.position_y = int(position.y)

    def move_point_2_to(self, position: core.Point2):
        self._wall_point_2.move_point_1_to(position)

    def _do_move_point_1_to(self, position: core.Point2):
        self._update_repeats_from_length_change(position)
        self.wall_previous_point._update_repeats_from_length_change(
            position, is_point_2=True
        )

        self.teleport_point_1_to(position)

    def _update_repeats_from_length_change(self, new_position: core.Point2, is_point_2=False):
        if is_point_2:
            end_point = self.point_1
        else:
            end_point = self.point_2

        delta_length = (end_point - new_position).length() - self.get_length()
        new_x_repeat = self.x_repeat + delta_length * self._LENGTH_REPEAT_SCALE
        self._wall.wall.repeat_x = editor.to_build_repeat_x(new_x_repeat)

    @property
    def targets(self):
        return self._targets

    @property
    def sector(self):
        return self._sector

    def get_sector(self):
        return self._sector

    def set_sector(self, value, new_wall_name: str):
        self._sector = value
        self._name = new_wall_name
        self.invalidate_geometry()

    @property
    def blood_wall(self):
        return self._wall

    @property
    def wall_point_2(self):
        return self._wall_point_2

    def set_wall_point_2(self, value: 'EditorWall'):
        self.invalidate_geometry()
        self._wall_point_2 = value

        value.invalidate_geometry()
        value.wall_previous_point = self

    @property
    def other_side_sector(self):
        if self._other_side_wall is None:
            return None
        return self._other_side_wall.sector

    @property
    def other_side_wall(self):
        return self._other_side_wall

    @property
    def point_1(self):
        return core.Point2(
            self._wall.wall.position_x,
            self._wall.wall.position_y
        )

    @property
    def origin_2d(self):
        return self.point_1

    @property
    def origin(self):
        return core.Point3(
            self.origin_2d.x,
            self.origin_2d.y,
            self._sector.floor_z_at_point(self.origin_2d)
        )

    @property
    def point_2(self):
        return self._wall_point_2.point_1

    @property
    def is_geometry(self):
        return False

    @property
    def line_segment(self):
        return segment.Segment(self.point_1, self.point_2)

    @property
    def is_destroyed(self):
        return self._is_destroyed

    def destroy(self):
        self._is_destroyed = True

    def get_type(self) -> int:
        return self._wall.wall.tags[0]

    def get_picnum(self, part: str):
        if part == self._MASK_WALL_PART:
            return self._wall.wall.over_picnum
        return self._wall.wall.picnum

    def set_picnum(self, part: str, picnum: int):
        self.invalidate_geometry()
        if part == self._MASK_WALL_PART:
            self._wall.wall.over_picnum = picnum
        else:
            self._wall.wall.picnum = picnum

    def show_debug(self):
        if self._debug_display is not None:
            self._debug_display.show()
            self._debug_display.hide(constants.SCENE_2D)

    def hide_debug(self):
        if self._debug_display is not None:
            self._debug_display.hide()

    def get_centre_2d(self) -> core.Point2:
        return self.line_segment.get_centre()

    def get_centre(self):
        centre = self.get_centre_2d() - self.get_normal() * 512
        height_centre = (self._sector.floor_z + self._sector.ceiling_z) / 2
        return core.Point3(centre.x, centre.y, height_centre)

    def get_normal(self) -> core.Vec2:
        return self.line_segment.get_normal()

    def get_orthogonal_vector(self) -> core.Vec2:
        return self.line_segment.get_orthogonal_vector()

    def get_direction(self) -> core.Vec2:
        return self.line_segment.get_direction()

    def get_direction_theta(self) -> float:
        return self.line_segment.get_direction_theta()

    def get_normalized_direction(self) -> core.Vec2:
        return self.line_segment.get_normalized_direction()

    def side_of_line(self, point: core.Point2):
        return self.line_segment.side_of_line(point)

    def intersect_line(self, point: core.Point3, direction: core.Vec3) -> core.Point2:
        direction_2d = core.Vec2(direction.x, direction.y)
        return self.line_segment.intersect_line(point.xy, direction_2d)

    def get_part_at_point(self, position: core.Point3):
        if self._other_side_wall is None:
            return f'{self._name}_full_highlight'

        lower_bottom = self._sector.floor_z_at_point(position.xy)
        lower_top = self.other_side_sector.floor_z_at_point(position.xy)

        if position.z <= lower_bottom and position.z >= lower_top:
            return f'{self._name}_lower_highlight'

        upper_bottom = self.other_side_sector.ceiling_z_at_point(position.xy)
        upper_top = self._sector.ceiling_z_at_point(position.xy)

        if position.z <= upper_bottom and position.z >= upper_top:
            return f'{self._name}_upper_highlight'

        return None

    def prepare_to_persist(
        self,
        sector_mapping: typing.Dict['editor.sector.EditorSector', int],
        wall_mapping: typing.Dict['editor.wall.EditorWall', int]
    ) -> map_data.wall.Wall:
        if self._other_side_wall is not None:
            self._wall.wall.other_side_wall_index = wall_mapping[self._other_side_wall]
        else:
            self._wall.wall.other_side_wall_index = -1

        if self.other_side_sector is not None:
            self._wall.wall.other_side_sector_index = sector_mapping[self.other_side_sector]
        else:
            self._wall.wall.other_side_sector_index = -1

        self._wall.wall.point2_index = wall_mapping[self._wall_point_2]

        return self._wall

    @property
    def rx_id(self):
        return self._wall.data.rx_id

    @property
    def tx_id(self):
        return self._wall.data.tx_id

    @property
    def x_repeat(self):
        return editor.to_repeat_x(self._wall.wall.repeat_x)

    @property
    def y_repeat(self):
        return editor.to_repeat_y(self._wall.wall.repeat_y)

    @property
    def x_panning(self):
        return editor.to_panning_x(self._wall.wall.panning_x)

    @property
    def y_panning(self):
        return editor.to_panning_y(self._wall.wall.panning_y)

    @property
    def shade(self):
        return editor.to_shade(self._wall.wall.shade)

    def get_shade(self, part: str):
        return self.shade

    def set_shade(self, part: str, value: float):
        self.invalidate_geometry()
        self._wall.wall.shade = editor.to_build_shade(value)

    def get_length(self):
        return self.get_direction().length()

    def reset_panning_and_repeats(self, part: str):
        self.invalidate_geometry()

        self._wall.wall.panning_x = 0
        self._wall.wall.panning_y = 0

        self._wall.wall.repeat_y = 8

        self._wall.wall.repeat_x = editor.to_build_repeat_x(
            self.get_length() * self._LENGTH_REPEAT_SCALE
        )

    def _make_wall_part(
        self,
        all_geometry: sector_geometry.SectorGeometry,
        part: str,
        floor_z: float,
        ceiling_z: float,
        floor_z_at_point_callback: typing.Callable[[core.Point2], float],
        ceiling_z_at_point_callback: typing.Callable[[core.Point2], float],
        picnum: int
    ):
        point_1_bottom = floor_z_at_point_callback(self.point_1)
        point_2_bottom = floor_z_at_point_callback(self.point_2)

        point_1_top = ceiling_z_at_point_callback(self.point_1)
        point_2_top = ceiling_z_at_point_callback(self.point_2)

        if point_1_top < point_1_bottom or point_2_top < point_2_bottom:
            vertex_data = core.GeomVertexData(
                part,
                constants.VERTEX_FORMAT,
                core.Geom.UH_static
            )
            vertex_data.set_num_rows(4)
            position_writer = core.GeomVertexWriter(vertex_data, 'vertex')
            colour_write = core.GeomVertexWriter(vertex_data, 'color')
            texcoord_writer = core.GeomVertexWriter(
                vertex_data,
                'texcoord'
            )

            colour_write.add_data4(self.shade, self.shade, self.shade, 1)
            colour_write.add_data4(self.shade, self.shade, self.shade, 1)
            colour_write.add_data4(self.shade, self.shade, self.shade, 1)
            colour_write.add_data4(self.shade, self.shade, self.shade, 1)

            texture_size = all_geometry.get_tile_dimensions(picnum)
            texture_coordinates = self._get_texture_coordinates(
                texture_size,
                floor_z,
                ceiling_z
            )

            position_writer.add_data3(
                self.point_1.x,
                self.point_1.y,
                point_1_bottom
            )
            texcoord_writer.add_data2(texture_coordinates[0], texture_coordinates[2])

            position_writer.add_data3(
                self.point_1.x,
                self.point_1.y,
                point_1_top
            )
            texcoord_writer.add_data2(texture_coordinates[0], texture_coordinates[3])

            position_writer.add_data3(
                self.point_2.x,
                self.point_2.y,
                point_2_top
            )
            texcoord_writer.add_data2(texture_coordinates[1], texture_coordinates[3])

            position_writer.add_data3(
                self.point_2.x,
                self.point_2.y,
                point_2_bottom
            )
            texcoord_writer.add_data2(texture_coordinates[1], texture_coordinates[2])

            primitive = core.GeomTriangles(core.Geom.UH_static)
            primitive.add_vertices(0, 2, 1)
            primitive.add_vertices(0, 3, 2)
            primitive.close_primitive()

            geometry = core.Geom(vertex_data)
            geometry.add_primitive(primitive)

            all_geometry.add_geometry(geometry, picnum, self._wall.wall.palette)
            highlight = all_geometry.add_highlight_geometry(
                geometry,
                f'{self._name}_{part}'
            )
            all_geometry.add_2d_highlight_geometry(
                highlight,
                self.point_1,
                self.point_2
            )

            return True

        return False

    def _get_texture_coordinates(
        self,
        texture_size: core.Vec2,
        floor_z: float,
        ceiling_z: float
    ):
        x_repeat = self.x_repeat
        y_repeat = (ceiling_z - floor_z) * self.y_repeat

        x_panning = self.x_panning
        y_panning = self.y_panning

        return (
            x_panning / texture_size.x,
            (x_panning + x_repeat) / texture_size.x,
            y_panning / texture_size.y,
            (y_panning + y_repeat) / texture_size.y
        )

    def _get_highlighter(self):
        return geometry_highlight
