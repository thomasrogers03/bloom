# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import bullet, core

from .. import constants, editor, game_map, map_data


class EditorWall:
    _MASK_WALL_PART = 'middle'

    def __init__(
        self,
        blood_wall: map_data.wall.Wall
    ):
        self._sector: 'editor.sector.EditorSector' = None
        self._wall = blood_wall
        self.wall_previous_point: EditorWall = None
        self._wall_point_2: EditorWall = None
        self._other_side_sector: 'editor.sector.EditorSector' = None
        self._other_side_wall: EditorWall = None
        self._scene: core.NodePath = None
        self._display: core.NodePath = None
        self._debug_display: core.NodePath = None
        self._vertex_format: core.GeomVertexFormat = None
        self._get_tile_callback: typing.Callable[[int], core.Texture] = None
        self._collision_world: bullet.BulletWorld = None
        self._texture_stage: core.TextureStage = None

    def setup(
        self,
        wall_point_2: 'editor.wall.EditorWall',
        other_side_sector: 'editor.sector.EditorSector',
        other_side_wall: 'editor.wall.EditorWall'
    ):
        self._wall_point_2 = wall_point_2
        self._other_side_sector = other_side_sector
        self._other_side_wall = other_side_wall
        self._needs_geometry_reset = False

    def setup_for_rendering(
        self,
        scene: core.NodePath,
        name: str,
        vertex_format: core.GeomVertexFormat,
        get_tile_callback: typing.Callable[[int], core.Texture]
    ):
        self._scene = scene
        self._display = self._scene.attach_new_node(name)
        self._vertex_format = vertex_format
        self._get_tile_callback = get_tile_callback
        self._texture_stage = core.TextureStage.get_default()

    def setup_geometry(self, sector: 'editor.sector.EditorSector', collision_world: bullet.BulletWorld):
        self._sector = sector
        self._collision_world = collision_world

        self._do_setup_geometry()

    def invalidate_geometry(self):
        if not self._needs_geometry_reset:
            self._needs_geometry_reset = True
            if self._other_side_wall is not None:
                self._other_side_wall.invalidate_geometry()

    def _do_setup_geometry(self):
        debug_display_node = core.TextNode('debug')
        text = f'Angle: {self.get_direction_theta()}\n'
        text += f'Direction: {self.get_direction()}\n'
        text += f'Length: {self.get_direction().length()}'
        debug_display_node.set_text(text)
        debug_display_node.set_align(core.TextNode.A_center)
        centre = self.get_centre() - self.get_normal() * 512
        height_centre = (self._sector.floor_z + self._sector.ceiling_z) / 2
        self._debug_display = self._display.attach_new_node(debug_display_node)
        self._debug_display.set_pos(centre.x, centre.y, height_centre)
        self._debug_display.set_billboard_axis()
        self._debug_display.set_scale(-96)
        self._debug_display.hide()
        
        segments_2d = core.LineSegs()
        segments_2d.set_thickness(2)
        segments_2d.draw_to(
            self.point_1.x,
            self.point_1.y,
            self._sector.floor_z - 16
        )
        segments_2d.draw_to(
            self.point_2.x,
            self.point_2.y,
            self._sector.floor_z - 16
        )
        display_2d_node = segments_2d.create('display_2d')
        display_2d: core.NodePath = self._display.attach_new_node(
            display_2d_node
        )
        display_2d.hide(constants.SCENE_3D)

        if self._other_side_sector is None:
            self._make_wall_part(
                'full',
                self._sector.floor_z,
                self._sector.ceiling_z,
                lambda point: self._sector.floor_z_at_point(point),
                lambda point: self._sector.ceiling_z_at_point(point),
                self._wall.wall.picnum
            )
        else:
            self._make_wall_part(
                'lower',
                self._sector.floor_z,
                self._other_side_sector.floor_z,
                lambda point: self._sector.floor_z_at_point(point),
                lambda point: self._other_side_sector.floor_z_at_point(point),
                self._wall.wall.picnum
            )
            self._make_wall_part(
                'upper',
                self._other_side_sector.ceiling_z,
                self._sector.ceiling_z,
                lambda point: self._other_side_sector.ceiling_z_at_point(point),
                lambda point: self._sector.ceiling_z_at_point(point),
                self._wall.wall.picnum
            )
            if self._wall.wall.stat.masking > 0 and self._wall.wall.over_picnum > 0:
                middle = self._make_wall_part(
                    self._MASK_WALL_PART,
                    self._other_side_sector.floor_z,
                    self._other_side_sector.ceiling_z,
                    lambda point: self._other_side_sector.floor_z_at_point(point),
                    lambda point: self._other_side_sector.ceiling_z_at_point(point),
                    self._wall.wall.over_picnum
                )
                if middle is not None:
                    middle.set_bin('transparent', 1)
                    middle.set_transparency(True)

                    if self._wall.wall.stat.translucent:
                        middle.set_color(1, 1, 1, 0.75)
                    elif self._wall.wall.stat.translucent_rev:
                        middle.set_color(1, 1, 1, 0.5)

        self._needs_geometry_reset = False

    def get_geometry_part(self, part: str) -> core.NodePath:
        return self._display.find(f'**/{part}')

    def extrude(self, sectors: typing.List['editor.sector.EditorSector']):
        from .sector import EditorSector

        if self._other_side_sector is not None:
            return

        new_sector = EditorSector(self._sector.sector.copy())
        new_sector_index = len(sectors)
        new_sector.setup_for_rendering(
            self._scene, 
            str(new_sector_index),
            self._vertex_format,
            self._get_tile_callback
        )
        sectors.append(new_sector)
        
        extrude_direction = self.get_normal() * 1024

        blood_point_1 = self._wall.copy()
        blood_point_1.wall.position_x = self._wall_point_2._wall.wall.position_x
        blood_point_1.wall.position_y = self._wall_point_2._wall.wall.position_y
        point_1 = EditorWall(blood_point_1)

        blood_point_2 = self._wall.copy()
        blood_point_2.wall.position_x = self._wall.wall.position_x
        blood_point_2.wall.position_y = self._wall.wall.position_y
        point_2 = EditorWall(blood_point_2)

        blood_point_3 = self._wall.copy()
        blood_point_3.wall.position_x = int(self._wall.wall.position_x + extrude_direction.x)
        blood_point_3.wall.position_y = int(self._wall.wall.position_y + extrude_direction.y)
        point_3 = EditorWall(blood_point_3)

        blood_point_4 = self._wall.copy()
        blood_point_4.wall.position_x = int(self._wall_point_2._wall.wall.position_x + extrude_direction.x)
        blood_point_4.wall.position_y = int(self._wall_point_2._wall.wall.position_y + extrude_direction.y)
        point_4 = EditorWall(blood_point_4)

        self._other_side_wall = point_1
        self._other_side_sector = new_sector

        point_1.wall_previous_point = point_4
        point_2.wall_previous_point = point_1
        point_3.wall_previous_point = point_2
        point_4.wall_previous_point = point_3

        new_segments = [
            (point_1, point_2), 
            (point_2, point_3), 
            (point_3, point_4), 
            (point_4, point_1)
        ]
        for new_wall, new_wall_point_2 in new_segments:
            new_wall.setup(
                new_wall_point_2,
                None,
                None
            )

            wall_index = new_sector.add_wall(new_wall)
            new_wall.setup_for_rendering(
                self._scene,
                str(wall_index),
                self._vertex_format,
                self._get_tile_callback
            )
        point_1._other_side_sector = self._sector
        point_1._other_side_wall = self
            
        self._sector.invalidate_geometry()
        self.invalidate_geometry()
        new_sector.setup_geometry(self._collision_world)

    def split(self, where: core.Point2):
        self._do_split(where)
        if self._other_side_wall is not None:
            self._other_side_wall = self._other_side_wall._do_split(where)

    def _do_split(self, where: core.Point2):
        self.invalidate_geometry()

        new_blood_wall = self._wall.copy()
        new_blood_wall.wall.position_x = int(where.x)
        new_blood_wall.wall.position_y = int(where.y)

        new_wall_point_2 = EditorWall(new_blood_wall)
        new_wall_point_2.wall_previous_point = self
        new_wall_point_2.setup(
            self._wall_point_2,
            self._other_side_sector,
            self._other_side_wall
        )

        self._wall_point_2.wall_previous_point = new_wall_point_2
        self._wall_point_2 = new_wall_point_2

        wall_index = self._sector.add_wall(new_wall_point_2)
        new_wall_point_2.setup_for_rendering(
            self._scene,
            str(wall_index),
            self._vertex_format,
            self._get_tile_callback
        )
        new_wall_point_2.setup_geometry(self._sector, self._collision_world)

        return new_wall_point_2

    def move_point_1_to(self, position: core.Point2):
        if self._other_side_wall is not None:
            self._other_side_wall.wall_point_2._do_move_point_1_to(position)
        elif self.wall_previous_point._other_side_wall is not None:
            self.wall_previous_point._other_side_wall._do_move_point_1_to(position)

        self._do_move_point_1_to(position)

    def move_point_2_to(self, position: core.Point2):
        self._wall_point_2.move_point_1_to(position)

    def _do_move_point_1_to(self, position: core.Point2):
        self._sector.invalidate_geometry()

        self._wall.wall.position_x = int(position.x)
        self._wall.wall.position_y = int(position.y)

    def reset_geometry_if_necessary(self):
        if not self._needs_geometry_reset:
            return

        collision_geometry: typing.Iterable[core.NodePath] = self._display.find_all_matches(
            '*_collision'
        )
        for node_path in collision_geometry:
            self._collision_world.remove(node_path.node())

        children: typing.Iterable[core.NodePath] = self._display.get_children()
        for node_path in children:
            node_path.remove_node()

        self._debug_display = None
        self._do_setup_geometry()

    @property
    def sector(self):
        return self._sector

    @property
    def wall_point_2(self):
        return self._wall_point_2

    @property
    def other_side_sector(self):
        return self._other_side_sector

    @property
    def point_1(self):
        return core.Point2(
            self._wall.wall.position_x,
            self._wall.wall.position_y
        )

    @property
    def point_2(self):
        return self._wall_point_2.point_1

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
        self._debug_display.show()
        self._debug_display.hide(constants.SCENE_2D)

    def hide_debug(self):
        self._debug_display.hide()

    def get_centre(self) -> core.Point2:
        return (self.point_1 + self.point_2) / 2

    def get_normal(self) -> core.Vec2:
        return self.get_orthogonal_vector().normalized()

    def get_orthogonal_vector(self) -> core.Vec2:
        centre = (self.point_1 + self.point_2) / 2
        direction = self.point_2 - self.point_1
        return core.Vec2(direction.y, -direction.x)

    def get_direction(self) -> core.Vec2:
        return self.point_2 - self.point_1

    def get_direction_theta(self) -> float:
        direction = self.get_direction()
        theta = math.atan2(direction.y, direction.x)
        return math.degrees(theta)

    def get_normalized_direction(self) -> core.Vec2:
        return self.get_direction().normalized()

    def side_of_line(self, point: core.Vec2):
        relative_point = point - self.point_1
        direction = self.get_orthogonal_vector().dot(relative_point)
        if direction > 0:
            return 1
        elif direction < 0:
            return -1
        return 0

    def prepare_to_persist(
        self,
        sector_mapping: typing.Dict['editor.sector.EditorSector', int],
        wall_mapping: typing.Dict['editor.wall.EditorWall', int]
    ) -> map_data.wall.Wall:
        if self._other_side_wall is not None:
            self._wall.wall.other_side_wall_index = wall_mapping[self._other_side_wall]
        else:
            self._wall.wall.other_side_wall_index = -1

        if self._other_side_sector is not None:
            self._wall.wall.other_side_sector_index = sector_mapping[self._other_side_sector]
        else:
            self._wall.wall.other_side_sector_index = -1

        self._wall.wall.point2_index = wall_mapping[self._wall_point_2]

        return self._wall

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

    def _make_wall_part(
        self,
        name: str,
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
                name,
                self._vertex_format,
                core.Geom.UH_static
            )
            vertex_data.set_num_rows(4)
            position_writer = core.GeomVertexWriter(vertex_data, 'vertex')
            texcoord_writer = core.GeomVertexWriter(
                vertex_data,
                'texcoord'
            )

            texture = self._get_tile_callback(picnum)
            texture_coordinates = self._get_texture_coordinates(
                texture,
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

            collision_mesh = bullet.BulletTriangleMesh()
            collision_mesh.add_geom(geometry)
            collision_mesh_shape = bullet.BulletTriangleMeshShape(
                collision_mesh,
                dynamic=False
            )

            bullet_node = bullet.BulletRigidBodyNode(f'{name}_collision')
            bullet_node.add_shape(collision_mesh_shape)
            self._collision_world.attach(bullet_node)
            bullet_node.set_python_tag('wall', self)
            bullet_node_path: core.NodePath = self._display.attach_new_node(
                bullet_node
            )

            direction_2d = self.get_orthogonal_vector()
            bullet_node.set_python_tag('direction', core.Vec3(
                direction_2d.x, direction_2d.y, 0))

            node = core.GeomNode(name)
            node.add_geom(geometry)

            shape: core.NodePath = bullet_node_path.attach_new_node(node)
            shape.set_bin('opaque', 2)
            shape.set_texture(texture)

            shape.hide(constants.SCENE_2D)

            return shape

        return None

    def _get_texture_coordinates(
        self,
        texture: core.Texture,
        floor_z: float,
        ceiling_z: float
    ):
        x_repeat = self.x_repeat
        y_repeat = (ceiling_z - floor_z) * self.y_repeat

        width = texture.get_x_size()
        height = texture.get_y_size()

        x_panning = self.x_panning
        y_panning = self.y_panning

        return (
            x_panning / width,
            (x_panning + x_repeat) / width,
            y_panning / height,
            (y_panning + y_repeat) / height
        )
