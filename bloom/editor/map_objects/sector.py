# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import bullet, core

from ... import audio, constants, editor, game_map, map_data
from .. import (event_grouping, marker_constants, plane, ror_constants,
                sector_geometry, segment, undo_stack)
from . import (empty_object, geometry_highlight, marker, sprite, wall,
               z_motion_marker)
from .drawing import sector as drawing_sector


class EditorSector(empty_object.EmptyObject):
    FLOOR_PART = 'floor_highlight'
    CEILING_PART = 'ceiling_highlight'

    def __init__(
        self,
        sector: map_data.sector.Sector,
        name: str,
        audio_manager: audio.Manager,
        geometry_factory: sector_geometry.SectorGeometryFactory,
        suggest_sky_picnum: typing.Callable[[int], int],
        undos: undo_stack.UndoStack
    ):
        super().__init__(undos)

        self._sector = sector
        self._name = name
        self._audio_manager = audio_manager
        self._geometry_factory = geometry_factory
        self._suggest_sky_picnum = suggest_sky_picnum

        self._below_ceiling_origin: core.Point3 = None
        self._above_floor_origin: core.Point3 = None

        self._sector_below_floor: EditorSector = None
        self._sector_above_ceiling: EditorSector = None

        self._is_destroyed = False

        self._walls: typing.List[wall.EditorWall] = []
        self._sprites: typing.List[sprite.EditorSprite] = []
        self._markers: typing.List[marker.EditorMarker] = [None, None]
        self._display: core.NodePath = None
        self._needs_geometry_reset = False

        self._floor_z_motion_markers: typing.List[marker.EditorMarker] = [
            z_motion_marker.EditorZMotionMarker(
                z_motion_marker.EditorZMotionMarker.POSITION_OFF,
                self.FLOOR_PART,
                self,
                self._undo_stack
            ),
            z_motion_marker.EditorZMotionMarker(
                z_motion_marker.EditorZMotionMarker.POSITION_ON,
                self.FLOOR_PART,
                self,
                self._undo_stack
            )
        ]
        self._ceiling_z_motion_markers: typing.List[marker.EditorMarker] = [
            z_motion_marker.EditorZMotionMarker(
                z_motion_marker.EditorZMotionMarker.POSITION_OFF,
                self.CEILING_PART,
                self,
                self._undo_stack
            ),
            z_motion_marker.EditorZMotionMarker(
                z_motion_marker.EditorZMotionMarker.POSITION_ON,
                self.CEILING_PART,
                self,
                self._undo_stack
            )
        ]

    def load(
        self,
        map_to_load: game_map.Map,
        sector_index: int,
        sprite_mapping: typing.Dict[int, sprite.EditorSprite],
        marker_sprite_mapping: typing.Dict[int, sprite.EditorSprite]
    ):
        for wall_index in self._wall_indices():
            self.add_wall(map_to_load.walls[wall_index])

        for sprite_index in self._sprite_indices(sector_index, map_to_load):
            editor_sprite = self.add_sprite(map_to_load.sprites[sprite_index])
            sprite_mapping[sprite_index] = editor_sprite
            if editor_sprite.sprite.sprite.velocity_x >= marker_constants.START_ID:
                if editor_sprite.sprite.sprite.tags[0] in marker_constants.MARKER_TYPES:
                    marker_sprite_mapping[editor_sprite.sprite.sprite.velocity_x] = editor_sprite
                else:
                    editor_sprite.sprite.sprite.velocity_x = 0

    def setup_walls_and_sprites_after_load(
        self,
        sectors: typing.List['EditorSector'],
        map_to_load: game_map.Map,
        lower_sectors: typing.Dict[int, 'EditorSector'],
        upper_sectors: typing.Dict[int, 'EditorSector'],
        sprite_mapping: typing.Dict[int, sprite.EditorSprite],
        marker_sprite_mapping: typing.Dict[int, sprite.EditorSprite]
    ):
        for wall_index in self._wall_indices():
            blood_wall = map_to_load.walls[wall_index]
            sector_wall_index = self._relative_wall_index(wall_index)

            if blood_wall.wall.other_side_sector_index < 0:
                other_side_sector: EditorSector = None
                other_side_wall: wall.EditorWall = None
            else:
                other_side_sector = sectors[blood_wall.wall.other_side_sector_index]
                other_side_wall = other_side_sector._wall_from_global_index(
                    blood_wall.wall.other_side_wall_index
                )

            point_1 = self._walls[sector_wall_index]
            point_2 = self._wall_from_global_index(
                blood_wall.wall.point2_index
            )
            point_2.wall_previous_point = point_1
            point_1.setup(
                point_2,
                other_side_wall
            )

        for editor_sprite in self._sprites:
            if editor_sprite.sprite.sprite.tags[0] in ror_constants.LOWER_LINK_TYPES:
                self._below_ceiling_origin = core.Point3(
                    editor_sprite.origin_2d.x,
                    editor_sprite.origin_2d.y,
                    self.ceiling_z_at_point(editor_sprite.origin_2d)
                )
                self._sector_above_ceiling = upper_sectors[editor_sprite.sprite.data.data1]
            elif editor_sprite.sprite.sprite.tags[0] in ror_constants.UPPER_LINK_TYPES:
                self._above_floor_origin = core.Point3(
                    editor_sprite.origin_2d.x,
                    editor_sprite.origin_2d.y,
                    self.floor_z_at_point(editor_sprite.origin_2d)
                )
                self._sector_below_floor = lower_sectors[editor_sprite.sprite.data.data1]

        for marker_index, marker_sprite_index in enumerate(self._sector.data.markers):
            if marker_sprite_index < 1:
                continue

            editor_sprite = marker_sprite_mapping.get(marker_sprite_index, None)
            if editor_sprite is None:
                continue

            sprite_type = editor_sprite.sprite.sprite.tags[0]
            if sprite_type not in marker_constants.MARKER_TYPES:
                raise AssertionError(
                    f'Invalid sprite type marker found: {sprite_type}')

            self.set_marker(marker_index, editor_sprite.sprite)
            editor_sprite.sector.remove_sprite(editor_sprite)

    def set_marker(self, marker_index: int, blood_sprite: map_data.sprite.Sprite):
        self._markers[marker_index] = marker.EditorMarker(
            blood_sprite,
            f'marker_{marker_index}',
            self,
            self._undo_stack
        )

    def setup_geometry(self):
        geometry = self._geometry_factory.new_geometry(self._name)
        for editor_wall in self._walls:
            editor_wall.setup_geometry(geometry)

        self._setup_sector_geometry(geometry)

        for sprite in self._sprites:
            sprite.setup_geometry(geometry)

        for editor_marker in self._markers:
            if editor_marker is not None:
                editor_marker.setup_geometry(geometry)

        for editor_marker in self._floor_z_motion_markers:
            editor_marker.setup_geometry(geometry)

        for editor_marker in self._ceiling_z_motion_markers:
            editor_marker.setup_geometry(geometry)

        self._display = geometry.build()
        self._needs_geometry_reset = False

    def validate(self):
        wall_set = set(self._walls)
        for editor_wall in self._walls:
            assert(not editor_wall.is_destroyed)
            assert(not editor_wall.line_segment.is_empty)

            if editor_wall.wall_point_2.wall_point_2 == editor_wall:
                messsage = f'Circular wall reference found: {editor_wall.point_1} -> {editor_wall.point_2} -> {editor_wall.wall_point_2.point_2}'
                raise AssertionError(messsage)
            if editor_wall.wall_previous_point.wall_previous_point == editor_wall:
                messsage = f'Circular wall reference found: {editor_wall.point_1} -> {editor_wall.wall_previous_point.point_1} -> {editor_wall.wall_previous_point.point_2}'
                raise AssertionError(messsage)

            assert(editor_wall.wall_point_2 in wall_set)
            assert(editor_wall.wall_point_2.sector == self)

            assert(editor_wall.wall_previous_point in wall_set)
            assert(editor_wall.wall_previous_point.sector == self)

    def destroy(self):
        if self._sector_below_floor is not None:
            self._sector_below_floor._sector_above_ceiling = None
        if self._sector_above_ceiling is not None:
            self._sector_above_ceiling._sector_below_floor = None
        self.invalidate_geometry()
        self._geometry_factory.remove_geometry(self._display)
        self._display = None
        self._is_destroyed = True

    def undestroy(self):
        self.invalidate_geometry()
        self._is_destroyed = False

    def reset_panning_and_repeats(self, part: str):
        self.invalidate_geometry()
        if part == self.FLOOR_PART:
            self._sector.sector.floor_stat.groudraw = 0
            self._sector.sector.floor_heinum = 0
            self._sector.sector.floor_xpanning = 0
            self._sector.sector.floor_ypanning = 0
        else:
            self._sector.sector.ceiling_stat.groudraw = 0
            self._sector.sector.ceiling_heinum = 0
            self._sector.sector.ceiling_xpanning = 0
            self._sector.sector.ceiling_ypanning = 0

    def reset_geometry_if_necessary(self):
        if not self._needs_geometry_reset:
            return

        self._geometry_factory.remove_geometry(self._display)
        self.setup_geometry()

    def get_below_draw_offset(self):
        return self._below_ceiling_origin - self._sector_above_ceiling._above_floor_origin

    def get_above_draw_offset(self):
        return self._above_floor_origin - self._sector_below_floor._below_ceiling_origin

    def set_draw_offset(self, position: core.Point3):
        if self._display is not None:
            self._display.set_pos(position)

    def get_geometry_part(self, part: str) -> core.NodePath:
        if self._display is None:
            return core.NodePath()
        return self._display.find(f'**/{part}')

    def get_animated_geometry(self) -> typing.Iterable[core.NodePath]:
        return self._display.find_all_matches('**/animated_geometry_*')

    def show(self):
        if self._display is not None:
            self._display.show()
            self._display.show(constants.SCENE_3D)

    @property
    def is_hidden(self):
        if self._display is None:
            return True
        return self._display.is_hidden(constants.SCENE_3D)

    def hide(self):
        if self._display is not None:
            self._display.set_pos(0, 0, 0)
            self._display.hide(constants.SCENE_3D)

    def adjacent_sectors(self) -> typing.List['EditorSector']:
        seen = {portal.other_side_sector for portal in self.portal_walls()}
        return list(seen)

    @property
    def markers(self) -> typing.List[marker.EditorMarker]:
        return self._markers

    @property
    def floor_z_motion_markers(self) -> typing.List[z_motion_marker.EditorZMotionMarker]:
        return self._floor_z_motion_markers

    @property
    def ceiling_z_motion_markers(self) -> typing.List[z_motion_marker.EditorZMotionMarker]:
        return self._ceiling_z_motion_markers

    @property
    def walls(self) -> typing.List[wall.EditorWall]:
        return self._walls

    @property
    def sprites(self) -> typing.List[sprite.EditorSprite]:
        return self._sprites

    def portal_walls(self) -> typing.Iterable[wall.EditorWall]:
        for editor_wall in self._walls:
            if editor_wall.other_side_sector is not None:
                yield editor_wall

    def invalidate_geometry(self):
        if not self._needs_geometry_reset:
            self._needs_geometry_reset = True
            for editor_wall in self._walls:
                editor_wall.invalidate_geometry()

    def move_floor_to(self, height: float):
        with self.change_blood_object():
            self._invalidate_adjacent_sectors()
            self._sector.sector.floor_z = editor.to_build_height(height)

    def move_ceiling_to(self, height: float):
        with self.change_blood_object():
            self._invalidate_adjacent_sectors()
            self._sector.sector.ceiling_z = editor.to_build_height(
                height
            )

    def swap_parallax(self, part: str):
        if part == self.FLOOR_PART:
            self._sector.sector.floor_stat.parallax = int(
                not self._sector.sector.floor_stat.parallax
            )
            if self._sector.sector.floor_stat.parallax:
                sky_picnum = self._suggest_sky_picnum(
                    self._sector.sector.floor_picnum
                )
                self._sector.sector.floor_picnum = sky_picnum
        else:
            self._sector.sector.ceiling_stat.parallax = int(
                not self._sector.sector.ceiling_stat.parallax
            )
            if self._sector.sector.ceiling_stat.parallax:
                sky_picnum = self._suggest_sky_picnum(
                    self._sector.sector.ceiling_picnum
                )
                self._sector.sector.ceiling_picnum = sky_picnum

        self.invalidate_geometry()
        self._invalidate_adjacent_sectors()

    def _invalidate_adjacent_sectors(self):
        for portal in self.portal_walls():
            portal.other_side_sector.invalidate_geometry()

    def get_data(self):
        return self._sector.data

    def get_stat_for_part(self, part: str):
        if part == self.FLOOR_PART:
            return self._sector.sector.floor_stat
        return self._sector.sector.ceiling_stat

    @property
    def default_part(self):
        return self.FLOOR_PART

    def get_all_parts(self):
        return [self.FLOOR_PART, self.CEILING_PART]

    def part_for_direction(self, direction: core.Vec3):
        if direction.z > 0:
            return self.FLOOR_PART
        return self.CEILING_PART

    def set_first_wall(self, editor_wall: wall.EditorWall):
        index = self._walls.index(editor_wall)
        if index == 0:
            return

        self.invalidate_geometry()

        old_first_wall = self._walls[0]
        self._walls[0] = editor_wall
        self._walls[index] = old_first_wall

    def prepare_to_persist(
        self,
        wall_mapping: typing.Dict[wall.EditorWall, int]
    ) -> map_data.sector.Sector:
        self._sector.sector.first_wall_index = wall_mapping[self._walls[0]]
        self._sector.sector.wall_count = len(self._walls)

        return self._sector

    def _setup_sector_geometry(self, geometry: sector_geometry.SectorGeometry):
        if len(self._walls) < 1:
            return

        self._add_geometry(
            geometry,
            'floor',
            self.floor_z_at_point,
            self.floor_x_panning,
            self.floor_y_panning,
            self._sector.sector.floor_stat,
            self._sector.sector.floor_picnum,
            self._sector.sector.floor_palette,
            self.floor_shade,
            self._sector.data.pan_floor
        )

        self._add_geometry(
            geometry,
            'ceiling',
            self.ceiling_z_at_point,
            self.ceiling_x_panning,
            self.ceiling_y_panning,
            self._sector.sector.ceiling_stat,
            self._sector.sector.ceiling_picnum,
            self._sector.sector.ceiling_palette,
            self.ceiling_shade,
            self._sector.data.pan_ceiling
        )

    def _add_geometry(
        self,
        all_geometry: sector_geometry.SectorGeometry,
        part: str,
        height_callback: typing.Callable[[core.Vec2], float],
        x_panning: float,
        y_panning: float,
        stat: map_data.sector.Stat,
        picnum: int,
        lookup: int,
        shade: float,
        pannable: bool
    ):
        for sub_sector in drawing_sector.Sector(self._walls).get_sub_sectors():
            polygon = drawing_sector.Sector.get_wall_bunch_points(
                sub_sector.outer_wall)
            self._cleanup_polygon(polygon)

            holes = []
            for wall in sub_sector.inner_walls:
                hole = drawing_sector.Sector.get_wall_bunch_points(wall)
                self._cleanup_polygon(hole)
                holes.append(hole)

            triangulator = core.Triangulator()
            for point in polygon:
                index = triangulator.add_vertex(point.x, point.y)
                triangulator.add_polygon_vertex(index)

            for hole in holes:
                triangulator.begin_hole()
                for point in hole:
                    index = triangulator.add_vertex(point.x, point.y)
                    triangulator.add_hole_vertex(index)
            triangulator.triangulate()

            vertex_data = core.GeomVertexData(
                'shape',
                constants.VERTEX_FORMAT,
                core.Geom.UH_static
            )
            vertex_data.set_num_rows(triangulator.get_num_vertices())
            position_writer = core.GeomVertexWriter(vertex_data, 'vertex')
            colour_writer = core.GeomVertexWriter(vertex_data, 'color')
            texcoord_writer = core.GeomVertexWriter(
                vertex_data,
                'texcoord'
            )

            first_wall = self._walls[0]
            direction_segment = first_wall.line_segment
            first_wall_orthogonal = first_wall.get_orthogonal_vector()
            orthogonal_segment = segment.Segment(
                first_wall.point_1, first_wall.point_1 + first_wall_orthogonal)

            texture_size = all_geometry.get_tile_dimensions(picnum)
            if texture_size.x < 1:
                texture_size.x = 1
            if texture_size.y < 1:
                texture_size.y = 1

            for point in triangulator.get_vertices():
                point_2d = core.Point2(point.x, point.y)
                position_writer.add_data3(
                    point_2d.x,
                    point_2d.y,
                    height_callback(point_2d)
                )
                colour_writer.add_data4(shade, shade, shade, 1)

                if stat.align:
                    new_y = direction_segment.get_point_distance(
                        point_2d, ignore_on_line=True)
                    new_x = orthogonal_segment.get_point_distance(
                        point_2d, ignore_on_line=True)
                    point_2d = core.Point2(new_x, new_y)

                if stat.swapxy:
                    y_offset = point_2d.x + x_panning
                    x_offset = point_2d.y + y_panning
                else:
                    x_offset = point_2d.x + x_panning
                    y_offset = point_2d.y + y_panning

                if stat.xflip:
                    x_offset = -x_offset
                if stat.yflip:
                    y_offset = -y_offset

                texture_coordinate_x = (x_offset / texture_size.x) / 16
                texture_coordinate_y = (y_offset / texture_size.y) / 16

                if stat.expand:
                    texture_coordinate_x *= 2
                    texture_coordinate_y *= 2

                texcoord_writer.add_data2(texture_coordinate_x, texture_coordinate_y)

            if part == 'floor':
                is_floor = True
            else:
                is_floor = False

            primitive = core.GeomTriangles(core.Geom.UH_static)
            if is_floor:
                for triangle_index in range(triangulator.get_num_triangles()):
                    primitive.add_vertices(
                        triangulator.get_triangle_v2(triangle_index),
                        triangulator.get_triangle_v1(triangle_index),
                        triangulator.get_triangle_v0(triangle_index)
                    )
            else:
                for triangle_index in range(triangulator.get_num_triangles()):
                    primitive.add_vertices(
                        triangulator.get_triangle_v0(triangle_index),
                        triangulator.get_triangle_v1(triangle_index),
                        triangulator.get_triangle_v2(triangle_index)
                    )
            primitive.close_primitive()

            geometry = core.Geom(vertex_data)
            geometry.add_primitive(primitive)

            if not stat.parallax and picnum != 504:
                all_geometry.add_geometry(geometry, picnum, lookup, pannable)
            all_geometry.add_highlight_geometry(
                geometry,
                part
            )

    @staticmethod
    def _cleanup_polygon(polygon: typing.List[core.Vec2]):
        point_count = len(polygon)
        index = 0
        while index < point_count:
            index_p2 = (index + 1) % point_count
            index_p3 = (index + 2) % point_count

            point_1 = polygon[index]
            point_2 = polygon[index_p2]
            point_3 = polygon[index_p3]

            direction_1 = (point_2 - point_1).normalized()
            direction_2 = (point_3 - point_2).normalized()

            if direction_1.dot(direction_2) < -0.99:
                del polygon[index_p2]
                point_count -= 1
            else:
                index += 1

    def _get_outer_most_wall(self):
        used_walls: typing.Set[wall.EditorWall] = set()
        outermost_wall: wall.EditorWall = None
        bounding_rectangle = core.Vec4(
            1 < 31,
            -(1 << 31),
            1 << 31,
            -(1 << 31)
        )

        for editor_wall in self._walls:
            while editor_wall not in used_walls:
                used_walls.add(editor_wall)

                if editor_wall.point_1.x < bounding_rectangle.x:
                    outermost_wall = editor_wall
                    bounding_rectangle.x = editor_wall.point_1.x
                if editor_wall.point_1.y < bounding_rectangle.z:
                    outermost_wall = editor_wall
                    bounding_rectangle.z = editor_wall.point_1.y

                if editor_wall.point_1.x > bounding_rectangle.y:
                    outermost_wall = editor_wall
                    bounding_rectangle.y = editor_wall.point_1.x
                if editor_wall.point_1.y > bounding_rectangle.w:
                    outermost_wall = editor_wall
                    bounding_rectangle.w = editor_wall.point_1.y

                editor_wall = editor_wall.wall_point_2

        return outermost_wall

    def _wall_from_global_index(self, index: int):
        relative_index = self._relative_wall_index(index)
        return self._walls[relative_index]

    def _relative_wall_index(self, index: int):
        return index - self._sector.sector.first_wall_index

    def _wall_indices(self):
        wall_index = self._sector.sector.first_wall_index
        wall_end = wall_index + self._sector.sector.wall_count
        while wall_index < wall_end:
            yield wall_index
            wall_index += 1

    def _sprite_indices(self, sector_index: int, map_to_load: game_map.Map):
        for sprite_index, sprite in enumerate(map_to_load.sprites):
            if sprite.sprite.sector_index == sector_index:
                yield sprite_index

    @property
    def _blood_object(self):
        return self._sector

    @_blood_object.setter
    def _blood_object(self, value):
        self._sector = value

    def get_sector(self):
        return self

    @property
    def rx_id(self):
        return self._sector.data.rx_id

    @property
    def tx_id(self):
        return self._sector.data.tx_id

    @property
    def ceiling_z(self):
        return editor.to_height(self._sector.sector.ceiling_z)

    @property
    def ceiling_heinum(self):
        return editor.to_heinum(self._sector.sector.ceiling_heinum)

    def get_heinum(self, part: str):
        if part == self.FLOOR_PART:
            return self.floor_heinum
        return self.ceiling_heinum

    def set_heinum(self, part: str, value: float):
        with self.change_blood_object():
            if part == self.FLOOR_PART:
                if value == 0:
                    self._sector.sector.floor_stat.groudraw = 0
                else:
                    self._sector.sector.floor_stat.groudraw = 1
                self._sector.sector.floor_heinum = editor.to_build_heinum(value)
            else:
                if value == 0:
                    self._sector.sector.ceiling_stat.groudraw = 0
                else:
                    self._sector.sector.ceiling_stat.groudraw = 1
                self._sector.sector.ceiling_heinum = editor.to_build_heinum(value)

    def ceiling_z_at_point(self, point: core.Point2):
        if not self._sector.sector.ceiling_stat.groudraw or len(self._walls) < 1:
            return self.ceiling_z

        normal = self._walls[0].get_normal()
        delta = point - self.origin_2d

        return self.ceiling_z + -self.ceiling_heinum * delta.dot(normal)

    def ceiling_slope_direction(self) -> core.Vec2:
        raise NotImplementedError()

    def get_shade(self, part: str):
        if part == self.FLOOR_PART:
            return self.floor_shade
        return self.ceiling_shade

    def set_shade(self, part: str, value: float):
        with self.change_blood_object():
            if part == self.FLOOR_PART:
                self._sector.sector.floor_shade = editor.to_build_shade(value)
            else:
                self._sector.sector.ceiling_shade = editor.to_build_shade(value)

    @property
    def ceiling_shade(self):
        return editor.to_shade(self._sector.sector.ceiling_shade)

    @property
    def floor_x_panning(self):
        return editor.to_panning_x(self._sector.sector.floor_xpanning)

    @property
    def floor_y_panning(self):
        return editor.to_panning_y(self._sector.sector.floor_ypanning)

    @property
    def ceiling_x_panning(self):
        return editor.to_panning_x(self._sector.sector.ceiling_xpanning)

    @property
    def ceiling_y_panning(self):
        return editor.to_panning_y(self._sector.sector.ceiling_ypanning)

    @property
    def floor_z(self):
        return editor.to_height(self._sector.sector.floor_z)

    @property
    def floor_heinum(self):
        return editor.to_heinum(self._sector.sector.floor_heinum)

    @property
    def floor_shade(self):
        return editor.to_shade(self._sector.sector.floor_shade)

    @property
    def sector(self):
        return self._sector

    @property
    def is_geometry(self):
        return True

    @property
    def floor_plane(self):
        point_1_2d = self.origin_2d
        point_2_2d = core.Point2(point_1_2d.x + 1, point_1_2d.y)
        point_3_2d = core.Point2(point_1_2d.x, point_1_2d.y + 1)
        return plane.Plane(
            core.Point3(
                point_1_2d.x,
                point_1_2d.y,
                self.floor_z_at_point(point_1_2d)
            ),
            core.Point3(
                point_2_2d.x,
                point_2_2d.y,
                self.floor_z_at_point(point_2_2d)
            ),
            core.Point3(
                point_3_2d.x,
                point_3_2d.y,
                self.floor_z_at_point(point_3_2d)
            )
        )

    @property
    def ceiling_plane(self):
        point_1_2d = self.origin_2d
        point_2_2d = core.Point2(point_1_2d.x + 1, point_1_2d.y)
        point_3_2d = core.Point2(point_1_2d.x, point_1_2d.y + 1)
        return plane.Plane(
            core.Point3(
                point_1_2d.x,
                point_1_2d.y,
                self.ceiling_z_at_point(point_1_2d)
            ),
            core.Point3(
                point_2_2d.x,
                point_2_2d.y,
                self.ceiling_z_at_point(point_2_2d)
            ),
            core.Point3(
                point_3_2d.x,
                point_3_2d.y,
                self.ceiling_z_at_point(point_3_2d)
            )
        )

    @property
    def origin_2d(self):
        return self._walls[0].point_1

    @property
    def origin(self):
        return core.Point3(
            self.origin_2d.x,
            self.origin_2d.y,
            self.floor_z
        )

    @property
    def sector_below_floor(self):
        return self._sector_below_floor

    @property
    def sector_above_ceiling(self):
        return self._sector_above_ceiling

    def link(self, part: str, new_sector: 'EditorSector', link_origin: core.Point3):
        if part == self.FLOOR_PART:
            self._sector.sector.floor_stat.parallax = 0
            self._sector_below_floor = new_sector
            self._above_floor_origin = link_origin
        else:
            self._sector.sector.ceiling_stat.parallax = 0
            self._sector_above_ceiling = new_sector
            self._below_ceiling_origin = link_origin

    def get_bounding_rectangle(self):
        result = core.Vec4(
            constants.REALLY_BIG_NUMBER,
            -constants.REALLY_BIG_NUMBER,
            constants.REALLY_BIG_NUMBER,
            -constants.REALLY_BIG_NUMBER,
        )
        for editor_wall in self._walls:
            result.x = min(result.x, editor_wall.point_1.x)
            result.y = max(result.y, editor_wall.point_1.x)
            result.z = min(result.z, editor_wall.point_1.y)
            result.w = max(result.w, editor_wall.point_1.y)
        return result

    def get_type(self) -> int:
        return self._sector.sector.tags[0]

    def get_picnum(self, part: str):
        if part == self.FLOOR_PART:
            return self._sector.sector.floor_picnum
        return self._sector.sector.ceiling_picnum

    def set_picnum(self, part: str, picnum: int):
        with self.change_blood_object():
            if part == self.FLOOR_PART:
                self._sector.sector.floor_picnum = picnum
            else:
                self._sector.sector.ceiling_picnum = picnum

    def remove_sprite(self, editor_sprite: sprite.EditorSprite):
        if self._is_destroyed:
            raise ValueError('Tried to remove sprite from destroyed sector!')

        self._sprites.remove(editor_sprite)
        editor_sprite.invalidate_geometry()

    def remove_wall(self, editor_wall: wall.EditorWall):
        if self._is_destroyed:
            raise ValueError('Tried to remove wall from destroyed sector!')

        self._walls.remove(editor_wall)
        editor_wall.invalidate_geometry()

    def add_wall(self, blood_wall: map_data.wall.Wall) -> wall.EditorWall:
        self.invalidate_geometry()

        new_wall_index = len(self._walls)
        new_wall = wall.EditorWall(
            blood_wall,
            str(new_wall_index),
            self,
            self._undo_stack
        )

        def _undo():
            self._walls.remove(new_wall)

        def _redo():
            self._walls.append(new_wall)

        self.change_attribute(_undo, _redo)
        return new_wall

    def migrate_wall_to_other_sector(
        self,
        wall_to_move: wall.EditorWall,
        new_sector: 'EditorSector'
    ):
        if self == new_sector:
            return

        self.invalidate_geometry()
        new_sector.invalidate_geometry()

        self._walls.remove(wall_to_move)
        for wall_index, editor_wall in enumerate(self._walls):
            editor_wall.set_sector(self, str(wall_index))

        new_sector._walls.append(wall_to_move)
        new_name = str(len(new_sector._walls))
        wall_to_move.set_sector(new_sector, new_name)

    def migrate_sprite_to_other_sector(
        self,
        sprite_to_move: sprite.EditorSprite,
        new_sector: 'EditorSector'
    ):
        if self == new_sector:
            return

        self.invalidate_geometry()
        new_sector.invalidate_geometry()

        self._sprites.remove(sprite_to_move)
        for sprite_index, editor_sprite in enumerate(self._sprites):
            editor_sprite.set_sector(self, str(sprite_index))

        new_sector._sprites.append(sprite_to_move)
        new_name = str(len(new_sector._sprites))
        sprite_to_move.set_sector(new_sector, new_name)

    def add_sprite(self, blood_sprite: map_data.sprite.Sprite):
        self.invalidate_geometry()

        new_sprite_index = len(self._sprites)
        new_sprite = sprite.EditorSprite(
            blood_sprite,
            str(new_sprite_index),
            self,
            self._audio_manager,
            self._geometry_factory.tile_manager,
            self._undo_stack
        )

        def _undo():
            self._sprites.remove(new_sprite)

        def _redo():
            self._sprites.append(new_sprite)

        self.change_attribute(_undo, _redo)
        return new_sprite

    def add_new_sprite(self, position: core.Point3):
        new_blood_sprite = map_data.sprite.Sprite.new()
        new_blood_sprite.sprite.position_x = int(position.x)
        new_blood_sprite.sprite.position_y = int(position.y)
        new_blood_sprite.sprite.position_z = editor.to_build_height(position.z)

        new_sprite = self.add_sprite(new_blood_sprite)
        z_offset = core.Vec3(0, 0, -new_sprite.size.y / 2)
        new_position = new_sprite.position + z_offset
        new_sprite.move_to(new_position)
        self.invalidate_geometry()

        return new_sprite

    def floor_z_at_point(self, point: core.Point2):
        if not self._sector.sector.floor_stat.groudraw or len(self._walls) < 1:
            return self.floor_z

        normal = self._walls[0].get_normal()
        delta = point - self.origin_2d

        return self.floor_z + -self.floor_heinum * delta.dot(normal)

    def floor_slope_direction(self) -> core.Vec2:
        point_2d_x = self.origin_2d + core.Point2(1, 0)
        point_2d_y = self.origin_2d + core.Point2(0, 1)

        x_z = self.floor_z_at_point(point_2d_x)
        y_z = self.floor_z_at_point(point_2d_y)

        theta_x = -math.atan2(x_z - self.floor_z, 1)
        theta_y = math.atan2(y_z - self.floor_z, 1)

        return core.Vec2(math.degrees(theta_x), math.degrees(theta_y))

    def vector_in_sector(self, position: core.Vec3):
        if position.z > self.floor_z or position.z < self.ceiling_z:
            return False

        return self.point_in_sector(position.xy)

    @property
    def can_see_above(self):
        return self._sector.sector.ceiling_picnum == 504

    @property
    def can_see_below(self):
        return self._sector.sector.floor_picnum == 504

    def point_in_sector(self, point: core.Point2):
        ray_start = core.Point2(-(1 << 31), point.y)
        intersecting = 0
        for editor_wall in self._walls:
            max_y = max(editor_wall.point_1.y, editor_wall.point_2.y)
            min_y = min(editor_wall.point_1.y, editor_wall.point_2.y)
            if min_y <= point.y and max_y > point.y:
                start_side = editor_wall.side_of_line(ray_start)
                side = editor_wall.side_of_line(point)
                if start_side != side:
                    intersecting += 1

        return intersecting % 2 == 1

    def _get_highlighter(self):
        return geometry_highlight
