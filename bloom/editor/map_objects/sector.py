# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing
from collections import defaultdict

from panda3d import bullet, core

from ... import constants, editor, game_map, map_data
from .. import plane, sector_geometry
from . import empty_object, geometry_highlight, sprite, wall


class SectorCollection:
    LOWER_LINK_TYPES = {6, 10, 12, 14}
    UPPER_LINK_TYPES = {7, 9, 11, 13}

    def __init__(
        self,
        map_to_load: game_map.Map,
        geometry_factory: sector_geometry.SectorGeometryFactory,
        suggest_sky_picnum: typing.Callable[[int], int]
    ):
        self._geometry_factory = geometry_factory
        self._suggest_sky_picnum = suggest_sky_picnum

        self._sectors: typing.List[EditorSector] = []
        self._targets: typing.Dict[int, list] = defaultdict(lambda: [])
        for sector_index, map_sector in enumerate(map_to_load.sectors):
            self.new_sector(map_sector).load(
                map_to_load,
                sector_index,
                self._targets
            )

        lower_sectors: typing.Dict[int, EditorSector] = {}
        upper_sectors: typing.Dict[int, EditorSector] = {}
        for blood_sprite in map_to_load.sprites:
            if blood_sprite.sprite.tags[0] in self.LOWER_LINK_TYPES:
                lower_sectors[blood_sprite.data.data1] = self._sectors[blood_sprite.sprite.sector_index]
            elif blood_sprite.sprite.tags[0] in self.UPPER_LINK_TYPES:
                upper_sectors[blood_sprite.data.data1] = self._sectors[blood_sprite.sprite.sector_index]

        for sector in self._sectors:
            sector.setup_walls_and_sprites_after_load(
                self._sectors,
                map_to_load,
                self._targets,
                lower_sectors,
                upper_sectors
            )

    @property
    def sectors(self) -> typing.List['EditorSector']:
        return self._sectors

    @property
    def suggest_sky_picnum(self):
        return self._suggest_sky_picnum

    def new_sector(self, blood_sector: game_map.sector.Sector):
        index = len(self._sectors)

        new_sector = EditorSector(
            self, blood_sector, str(index), self._geometry_factory)
        self._sectors.append(new_sector)

        return new_sector

    def setup_geometry(self):
        for sector in self._sectors:
            sector.setup_geometry()


class EditorSector(empty_object.EmptyObject):
    FLOOR_PART = 'floor_highlight'
    CEILING_PART = 'ceiling_highlight'

    def __init__(
        self,
        sector_collection: SectorCollection,
        sector: map_data.sector.Sector,
        name: str,
        geometry_factory: sector_geometry.SectorGeometryFactory
    ):
        self._sector_collection = sector_collection
        self._sector = sector
        self._name = name
        self._geometry_factory = geometry_factory
        self._targets = []

        self._below_ceiling_origin: core.Point3 = None
        self._above_floor_origin: core.Point3 = None

        self._sector_below_floor: EditorSector = None
        self._sector_above_ceiling: EditorSector = None

        self._walls: typing.List[wall.EditorWall] = []
        self._sprites: typing.List[sprite.EditorSprite] = []
        self._display: core.NodePath = None
        self._needs_geometry_reset = False

    def load(
        self,
        map_to_load: game_map.Map,
        sector_index: int,
        targets: typing.Dict[int, list]
    ):
        if self.rx_id > 0:
            targets[self.rx_id].append(self)

        for wall_index in self._wall_indices():
            new_wall = self.add_wall(map_to_load.walls[wall_index])
            if new_wall.rx_id > 0:
                targets[new_wall.rx_id].append(new_wall)

        for sprite_index in self._sprite_indices(sector_index, map_to_load):
            new_sprite = self.add_sprite(map_to_load.sprites[sprite_index])
            if new_sprite.rx_id > 0:
                targets[new_sprite.rx_id].append(new_sprite)

    def setup_walls_and_sprites_after_load(
        self,
        sectors: typing.List['EditorSector'],
        map_to_load: game_map.Map,
        targets: typing.Dict[int, list],
        lower_sectors: typing.Dict[int, 'EditorSector'],
        upper_sectors: typing.Dict[int, 'EditorSector']
    ):
        self._targets = targets[self.tx_id]

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
                other_side_wall,
                targets[point_1.tx_id]
            )

        for editor_sprite in self._sprites:
            editor_sprite.setup(targets[editor_sprite.tx_id])
            if editor_sprite.sprite.sprite.tags[0] in SectorCollection.LOWER_LINK_TYPES:
                self._below_ceiling_origin = core.Point3(
                    editor_sprite.origin_2d.x,
                    editor_sprite.origin_2d.y,
                    self.ceiling_z_at_point(editor_sprite.origin_2d)
                )
                self._sector_above_ceiling = upper_sectors[editor_sprite.sprite.data.data1]
            elif editor_sprite.sprite.sprite.tags[0] in SectorCollection.UPPER_LINK_TYPES:
                self._above_floor_origin = core.Point3(
                    editor_sprite.origin_2d.x,
                    editor_sprite.origin_2d.y,
                    self.floor_z_at_point(editor_sprite.origin_2d)
                )
                self._sector_below_floor = lower_sectors[editor_sprite.sprite.data.data1]

    def setup_geometry(self):
        geometry = self._geometry_factory.new_geometry(self._name)
        for editor_wall in self._walls:
            editor_wall.setup_geometry(geometry)

        self._setup_sector_geometry(geometry)

        for sprite in self._sprites:
            sprite.setup_geometry(geometry)

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
        self._sector_collection.sectors.remove(self)

    def reset_panning_and_repeats(self, part: str):
        self.invalidate_geometry()
        if part == self.FLOOR_PART:
            self._sector.sector.floor_stat.groudraw = 0
            self._sector.sector.floor_heinum = 0
        else:
            self._sector.sector.ceiling_stat.groudraw = 0
            self._sector.sector.ceiling_heinum = 0

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
        return self._display.find_all_matches('**/animated_geometry')

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

    def adjacent_sectors(self) -> typing.List['editor.sector.EditorSector']:
        seen = {portal.other_side_sector for portal in self.portal_walls()}
        return list(seen)

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
        self.invalidate_geometry()
        self._invalidate_adjacent_sectors()
        self._sector.sector.floor_z = editor.to_build_height(height)

    def move_ceiling_to(self, height: float):
        self.invalidate_geometry()
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
                sky_picnum = self._sector_collection.suggest_sky_picnum(
                    self._sector.sector.floor_picnum
                )
                self._sector.sector.floor_picnum = sky_picnum
        else:
            self._sector.sector.ceiling_stat.parallax = int(
                not self._sector.sector.ceiling_stat.parallax
            )
            if self._sector.sector.ceiling_stat.parallax:
                sky_picnum = self._sector_collection.suggest_sky_picnum(
                    self._sector.sector.ceiling_picnum
                )
                self._sector.sector.ceiling_picnum = sky_picnum

        self.invalidate_geometry()
        self._invalidate_adjacent_sectors()

    def _invalidate_adjacent_sectors(self):
        for portal in self.portal_walls():
            portal.other_side_sector.invalidate_geometry()

    def new_sector(self):
        new_sector = self._sector_collection.new_sector(self._sector.copy())
        new_sector.setup_geometry()

        return new_sector

    @staticmethod
    def prepare_to_persist(
        find_sector: typing.Callable[['editor.sector.EditorSector', core.Point3], 'editor.sector.EditorSector'],
        sectors: typing.List['editor.sector.EditorSector'],
        builder_position: core.Point3
    ):
        blood_sectors: typing.List[map_data.sector.Sector] = []
        blood_walls: typing.List[map_data.wall.Wall] = []
        blood_sprites: typing.List[map_data.sprite.Sprite] = []

        sector_index_mapping: typing.Dict[EditorSector, int] = {}
        wall_index_mapping: typing.Dict[wall.EditorWall, int] = {}

        for sector_index, sector in enumerate(sectors):
            sector_index_mapping[sector] = sector_index
            for wall in sector._walls:
                wall_index_mapping[wall] = len(wall_index_mapping)

        for sector in sectors:
            for wall in sector._walls:
                blood_wall = wall.prepare_to_persist(
                    sector_index_mapping, wall_index_mapping)
                blood_walls.append(blood_wall)

            for sprite in sector._sprites:
                blood_sprite = sprite.prepare_to_persist(
                    find_sector, sector_index_mapping)
                blood_sprites.append(blood_sprite)

            blood_sector = sector._prepare_to_persist(wall_index_mapping)
            blood_sectors.append(blood_sector)

        builder_sector = find_sector(None, builder_position)
        if builder_sector is not None:
            builder_sector_index = sector_index_mapping[builder_sector]
        else:
            builder_sector_index = -1

        return blood_sectors, blood_walls, blood_sprites, builder_sector_index

    def part_for_direction(self, direction: core.Vec3):
        if direction.z > 0:
            return self.FLOOR_PART
        return self.CEILING_PART

    def _prepare_to_persist(self, wall_mapping: typing.Dict[wall.EditorWall, int]) -> map_data.sector.Sector:
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
            self.floor_shade
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
            self.ceiling_shade
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
        shade: float
    ):
        polygon, holes = self._get_polygon_and_holes()

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

        texture_size = all_geometry.get_tile_dimensions(picnum)
        for point in triangulator.get_vertices():
            point_2d = core.Point2(point.x, point.y)
            position_writer.add_data3(point_2d.x, point_2d.y, height_callback(point_2d))
            colour_writer.add_data4(shade, shade, shade, 1)

            if stat.swapxy:
                y_offset = point.x + x_panning
                x_offset = point.y + y_panning
            else:
                x_offset = point.x + x_panning
                y_offset = point.y + y_panning

            if stat.xflip:
                x_offset = -x_offset
            if stat.yflip:
                y_offset = -y_offset

            texture_coordinate_x = (x_offset / texture_size.x) / 16
            texture_coordinate_y = (y_offset / texture_size.y) / 16

            if stat.expand:
                texture_coordinate_x /= 2
                texture_coordinate_y /= 2

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
            all_geometry.add_geometry(geometry, picnum, lookup)
        all_geometry.add_highlight_geometry(
            geometry,
            part
        )

    def _get_polygon_and_holes(self):
        outer_most_wall = self._get_outer_most_wall()
        used_walls: typing.Set[wall.EditorWall] = set()

        polygon: typing.List[core.Vec2] = list(
            self._closed_polygon_from_wall(
                outer_most_wall,
                used_walls
            )
        )
        self._cleanup_polygon(polygon)

        holes: typing.List[typing.List[core.Vec2]] = []
        for editor_wall in self._walls:
            if editor_wall not in used_walls:
                hole = list(
                    self._closed_polygon_from_wall(
                        editor_wall, used_walls
                    )
                )
                self._cleanup_polygon(hole)
                holes.append(hole)

        return polygon, holes

    def _closed_polygon_from_wall(self, editor_wall: wall.EditorWall, used_walls: typing.Set[wall.EditorWall]):
        while editor_wall not in used_walls:
            used_walls.add(editor_wall)
            yield editor_wall.point_1
            editor_wall = editor_wall.wall_point_2

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
        pass

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
        self.invalidate_geometry()
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
        self.invalidate_geometry()
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
    def targets(self):
        return self._targets

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

    def get_type(self) -> int:
        return self._sector.sector.tags[0]

    def get_picnum(self, part: str):
        if part == self.FLOOR_PART:
            return self._sector.sector.floor_picnum
        return self._sector.sector.ceiling_picnum

    def set_picnum(self, part: str, picnum: int):
        self.invalidate_geometry()
        if part == self.FLOOR_PART:
            self._sector.sector.floor_picnum = picnum
        else:
            self._sector.sector.ceiling_picnum = picnum

    def remove_sprite(self, editor_sprite: sprite.EditorSprite):
        self._sprites.remove(editor_sprite)
        editor_sprite.invalidate_geometry()

    def remove_wall(self, editor_wall: wall.EditorWall):
        self._walls.remove(editor_wall)
        editor_wall.invalidate_geometry()

    def add_wall(self, blood_wall: map_data.wall.Wall) -> wall.EditorWall:
        self.invalidate_geometry()

        new_wall_index = len(self._walls)
        new_wall = wall.EditorWall(blood_wall, str(new_wall_index), self)
        self._walls.append(new_wall)

        return new_wall
    
    def migrate_wall_to_other_sector(
        self, 
        wall_to_move: wall.EditorWall,
        new_sector: 'EditorSector'
    ):
        self.invalidate_geometry()
        new_sector.invalidate_geometry()

        self._walls.remove(wall_to_move)
        for wall_index, editor_wall in enumerate(self._walls):
            editor_wall.set_sector(self, str(wall_index))

        new_sector._walls.append(wall_to_move)
        new_name = str(len(new_sector._walls))
        wall_to_move.set_sector(new_sector, new_name)

    def add_sprite(self, blood_sprite: map_data.sprite.Sprite):
        self.invalidate_geometry()

        new_sprite_index = len(self._sprites)
        new_sprite = sprite.EditorSprite(
            blood_sprite,
            str(new_sprite_index),
            self,
            self._geometry_factory.tile_manager
        )
        self._sprites.append(new_sprite)

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
        for wall in self._walls:
            max_y = max(wall.point_1.y, wall.point_2.y)
            min_y = min(wall.point_1.y, wall.point_2.y)
            if min_y <= point.y and max_y >= point.y:
                start_side = wall.side_of_line(ray_start)
                side = wall.side_of_line(point)
                if start_side != side:
                    intersecting += 1

        return intersecting % 2 == 1

    def _get_highlighter(self):
        return geometry_highlight
