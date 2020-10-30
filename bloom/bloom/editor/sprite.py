# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import bullet, core

from .. import constants, editor, game_map, map_data


class EditorSprite:

    def __init__(
        self,
        sprite_index: int,
        map_to_load: game_map.Map
    ):
        self._sector: 'editor.sector.EditorSector' = None
        self._sprite = map_to_load.sprites[sprite_index]
        self._display: core.NodePath = None
        self._positioner: core.NodePath = None
        self._vertex_format: core.GeomVertexFormat = None
        self._get_tile_callback: typing.Callable[[int], core.Texture] = None
        self._collision_world: bullet.BulletWorld = None
        self._texture_stage: core.TextureStage = None

    def setup(self, sector: 'editor.sector.EditorSector'):
        self._sector = sector

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
        self._texture_stage = core.TextureStage.get_default()

    def setup_geometry(self, collision_world: bullet.BulletWorld):
        self._collision_world = collision_world
        self._make_sprite_part()

    def get_geometry_part(self, part: str) -> core.NodePath:
        return self._display.find(f'**/{part}')

    @property
    def position(self):
        return core.Point3(
            self._sprite.sprite.position_x,
            self._sprite.sprite.position_y,
            editor.to_height(self._sprite.sprite.position_z),
        )

    @property
    def theta(self):
        return editor.to_degrees(self._sprite.sprite.theta)

    def get_direction(self) -> core.Vec2:
        sin_theta = math.sin(math.radians(self.theta))
        cos_theta = math.cos(math.radians(self.theta))

        return core.Vec2(-sin_theta, cos_theta)

    @property
    def x_repeat(self):
        return editor.to_sprite_repeat(self._sprite.sprite.repeat_x)

    @property
    def y_repeat(self):
        return editor.to_sprite_repeat(self._sprite.sprite.repeat_y)

    @property
    def sector(self):
        return self._sector

    @property
    def is_geometry(self):
        return False

    def reset_panning_and_repeats(self):
        pass

    def swap_parallax(self, part: str):
        pass

    def _make_sprite_part(self):
        texture = self._get_tile_callback(self._sprite.sprite.picnum)
        texture_width = texture.get_x_size()
        texture_height = texture.get_y_size()

        card_maker = core.CardMaker('sprite')
        frame = core.Vec4(0.5, -0.5, 0, 1)
        card_maker.set_frame(frame)

        if self._sprite.sprite.stat.facing > 0:
            collision_mesh = bullet.BulletTriangleMesh()
            collision_mesh.add_triangle(
                core.Vec3(-0.5, -0.5),
                core.Vec3(-0.5, 0.5),
                core.Vec3(0.5, 0.5),
            )
            collision_mesh.add_triangle(
                core.Vec3(-0.5, -0.5),
                core.Vec3(0.5, 0.5),
                core.Vec3(0.5, -0.5),
            )
            collision_mesh_shape = bullet.BulletTriangleMeshShape(
                collision_mesh,
                dynamic=False
            )
        else:
            collision_mesh_shape = bullet.BulletCylinderShape(
                0.5,
                1,
                bullet.Z_up
            )

        bullet_node = bullet.BulletRigidBodyNode(f'sprite_collision')
        bullet_node.add_shape(collision_mesh_shape)
        self._collision_world.attach(bullet_node)
        bullet_node.set_python_tag('sprite', self)
        bullet_node_path: core.NodePath = self._display.attach_new_node(
            bullet_node
        )
        bullet_node_path.set_pos(self.position)
        bullet_node_path.set_scale(
            texture_width * self.x_repeat,
            1,
            texture_height * self.y_repeat,
        )
        bullet_node_path.set_h(self.theta)

        if self._sprite.sprite.stat.facing == 0:
            bullet_node_path.set_billboard_axis()
            bullet_node_path.set_h(0)
        elif self._sprite.sprite.stat.facing == 2:
            bullet_node_path.set_p(90)

        self._positioner = bullet_node_path

        card_node = card_maker.generate()
        card: core.NodePath = bullet_node_path.attach_new_node(card_node)
        card.set_transparency(True)
        card.set_bin('transparent', 1)

        card.set_texture(texture, 1)
        if self._sprite.sprite.stat.centring:
            card.set_z(-0.5)

        if not self._sprite.sprite.stat.one_sided:
            card.set_two_sided(True)

        card.set_depth_offset(2, 1)

        return card

    def move_to(self, position: core.Point3):
        self._positioner.set_pos(position)
        self._sprite.sprite.position_x = int(position.x)
        self._sprite.sprite.position_y = int(position.y)
        self._sprite.sprite.position_z = editor.to_build_height(position.z)

    def show_debug(self):
        pass

    def hide_debug(self):
        pass

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
