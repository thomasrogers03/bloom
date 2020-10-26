# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

import constants
import game_map
import map_data.sector
import map_data.sprite
import map_data.wall
from panda3d import bullet, core

import editor

from . import sprite, wall


class EditorSector:

    def __init__(
        self,
        sector: map_data.sector.Sector
    ):
        self._sector = sector
        self._walls: typing.List[wall.EditorWall] = []
        self._sprites: typing.List[sprite.EditorSprite] = []
        self._vertex_format: core.GeomVertexFormat = None
        self._display: core.NodePath = None
        self._floor: core.NodePath = None
        self._ceiling: core.NodePath = None
        self._get_tile_callback: typing.Callable[[int], core.Texture] = None
        self._collision_world: bullet.BulletWorld = None
        self._needs_geometry_reset = False

    def load(
        self,
        sector_index: int,
        map_to_load: game_map.Map
    ):
        self._walls = [
            wall.EditorWall(map_to_load.walls[wall_index])
            for wall_index in self._wall_indices()
        ]
        self._sprites = [
            sprite.EditorSprite(sprite_index, map_to_load)
            for sprite_index in self._sprite_indices(sector_index, map_to_load)
        ]

        return self

    def setup_walls_and_sprites_after_load(
        self,
        sectors: typing.List['editor.sector.EditorSector'],
        map_to_load: game_map.Map
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
                other_side_sector,
                other_side_wall
            )

        for sprite in self._sprites:
            sprite.setup(self)

    def setup_for_rendering(
        self,
        scene: core.NodePath,
        name: str,
        vertex_format: core.GeomVertexFormat,
        get_tile_callback: typing.Callable[[int], core.Texture]
    ):
        self._display = scene.attach_new_node(name)
        self._vertex_format = vertex_format
        self._get_tile_callback = get_tile_callback

        wall_display = self._display.attach_new_node('walls')
        for wall_index, editor_wall in enumerate(self._walls):
            editor_wall.setup_for_rendering(
                wall_display,
                str(wall_index),
                vertex_format,
                get_tile_callback
            )

        sprite_display = self._display.attach_new_node('sprites')
        for sprite_index, sprite in enumerate(self._sprites):
            sprite.setup_for_rendering(
                sprite_display,
                str(sprite_index),
                vertex_format,
                get_tile_callback
            )

    def setup_geometry(self, collision_world: bullet.BulletWorld):
        self._collision_world = collision_world

        for editor_wall in self._walls:
            editor_wall.setup_geometry(self, self._collision_world)

        for sprite in self._sprites:
            sprite.setup_geometry(self._collision_world)

        self._setup_sector_geometry()

    def reset_geometry_if_necessary(self):
        for editor_wall in self._walls:
            editor_wall.reset_geometry_if_necessary()

        if not self._needs_geometry_reset:
            return

        floor_collision: bullet.BulletRigidBodyNode = self._display.find(
            'floor_collision'
        )
        self._collision_world.remove(floor_collision.node())
        self._floor.remove_node()
        self._floor = None

        ceiling_collision: bullet.BulletRigidBodyNode = self._display.find(
            'ceiling_collision'
        )
        self._collision_world.remove(ceiling_collision.node())
        self._ceiling.remove_node()
        self._ceiling = None

        self._setup_sector_geometry()

    def get_geometry_part(self, part: str) -> core.NodePath:
        return self._display.find(f'**/{part}')

    def show(self):
        self._display.show(constants.SCENE_3D)
        self._floor.show(constants.SCENE_2D)

    def hide(self):
        self._display.hide(constants.SCENE_3D)
        self._floor.hide(constants.SCENE_2D)

    def adjacent_sectors(self) -> typing.List['editor.sector.EditorSector']:
        seen = {portal.other_side_sector for portal in self.portal_walls()}
        return list(seen)

    def portal_walls(self) -> typing.Iterable[wall.EditorWall]:
        for editor_wall in self._walls:
            if editor_wall.other_side_sector is not None:
                yield editor_wall

    def invalidate_geometry(self):
        if not self._needs_geometry_reset:
            self._needs_geometry_reset = True
            for wall in self._walls:
                wall.invalidate_geometry()

    def move_floor_to(self, height: float):
        self.invalidate_geometry()
        self._sector.sector.floor_z = editor.to_build_height(height)

    def move_ceiling_to(self, height: float):
        self.invalidate_geometry()
        self._sector.sector.ceiling_z = editor.to_build_height(
            height
        )

    def show_debug(self):
        pass

    def hide_debug(self):
        pass

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

    def _prepare_to_persist(self, wall_mapping: typing.Dict[wall.EditorWall, int]) -> map_data.sector.Sector:
        self._sector.sector.first_wall_index = wall_mapping[self._walls[0]]
        self._sector.sector.wall_count = len(self._walls)

        return self._sector

    def _setup_sector_geometry(self):
        self._floor = self._get_triangulated_sector_shape(
            'floor', self.floor_z_at_point,
            self.floor_x_panning,
            self.floor_y_panning,
            self._sector.sector.floor_stat,
            self._sector.sector.floor_picnum
        )
        self._floor.set_attrib(
            core.CullFaceAttrib.make(
                core.CullFaceAttrib.M_cull_counter_clockwise
            )
        )

        self._ceiling = self._get_triangulated_sector_shape(
            'ceiling', self.ceiling_z_at_point,
            self.ceiling_x_panning,
            self.ceiling_y_panning,
            self._sector.sector.ceiling_stat,self._sector.sector.ceiling_picnum
        )
        self._ceiling.hide(constants.SCENE_2D)

        self._needs_geometry_reset = False

    def _get_triangulated_sector_shape(
        self,
        part: str,
        height_callback: typing.Callable[[core.Vec2], float],
        x_panning: float,
        y_panning: float,
        stat: map_data.sector.Stat,
        picnum: int
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
            self._vertex_format,
            core.Geom.UH_static
        )
        vertex_data.set_num_rows(triangulator.get_num_vertices())
        position_writer = core.GeomVertexWriter(vertex_data, 'vertex')
        texcoord_writer = core.GeomVertexWriter(
            vertex_data,
            'texcoord'
        )

        texture = self._get_tile_callback(picnum)
        for point in triangulator.get_vertices():
            point = core.Point2(point.x, point.y)
            position_writer.add_data3(point.x, point.y, height_callback(point))

            texture_coordinate_x = ((point.x + x_panning) * texture.get_x_size() ) / (1_000 * 128)
            texture_coordinate_y = ((point.y + y_panning) * texture.get_y_size() ) / (1_000 * 128)

            if stat.expand:
                texture_coordinate_x *= 2
                texture_coordinate_y *= 2

            if stat.swapxy:
                texcoord_writer.add_data2(texture_coordinate_y, texture_coordinate_x)
            else:
                texcoord_writer.add_data2(texture_coordinate_x, texture_coordinate_y)

        primitive = core.GeomTriangles(core.Geom.UH_static)
        for triangle_index in range(triangulator.get_num_triangles()):
            primitive.add_vertices(
                triangulator.get_triangle_v0(triangle_index),
                triangulator.get_triangle_v1(triangle_index),
                triangulator.get_triangle_v2(triangle_index)
            )
        primitive.close_primitive()

        geometry = core.Geom(vertex_data)
        geometry.add_primitive(primitive)

        collision_mesh = bullet.BulletTriangleMesh()
        collision_mesh.add_geom(geometry)
        collision_mesh_shape = bullet.BulletTriangleMeshShape(
            collision_mesh,
            dynamic=False
        )

        collision_node = bullet.BulletRigidBodyNode(f'{part}_collision')
        collision_node.add_shape(collision_mesh_shape)
        collision_node.set_python_tag('sector', self)
        self._collision_world.attach(collision_node)
        collision = self._display.attach_new_node(collision_node)

        if part == 'floor':
            collision_node.set_python_tag('direction', core.Vec3(0, 0, 1))
        else:
            collision_node.set_python_tag('direction', core.Vec3(0, 0, -1))

        node = core.GeomNode(part)
        node.add_geom(geometry)
        sector_shape: core.NodePath = collision.attach_new_node(node)
        sector_shape.set_bin('opaque', 2)
        sector_shape.set_texture(texture, 1)

        return sector_shape

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

    @property
    def ceiling_z(self):
        return editor.to_height(self._sector.sector.ceiling_z)

    @property
    def ceiling_heinum(self):
        return editor.to_heinum(self._sector.sector.ceiling_heinum)

    def ceiling_z_at_point(self, point: core.Point2):
        if not self._sector.sector.ceiling_stat.groudraw:
            return self.ceiling_z

        normal = self._walls[0].get_normal()
        delta = point - self._walls[0].point_1

        return self.ceiling_z + -self.ceiling_heinum * delta.dot(normal)

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
    def sector(self):
        return self._sector

    def add_wall(self, new_wall: wall.EditorWall):
        self.invalidate_geometry()

        new_wall_index = len(self._walls)
        self._walls.append(new_wall)

        return new_wall_index

    def floor_z_at_point(self, point: core.Point2):
        if not self._sector.sector.floor_stat.groudraw:
            return self.floor_z

        normal = self._walls[0].get_normal()
        delta = point - self._walls[0].point_1

        return self.floor_z + -self.floor_heinum * delta.dot(normal)

    def vector_in_sector(self, position: core.Vec3):
        if position.z > self.floor_z or position.z < self.ceiling_z:
            return False

        return self._point_in_sector(core.Point2(position.x, position.y))

    def _point_in_sector(self, point: core.Point2):
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
