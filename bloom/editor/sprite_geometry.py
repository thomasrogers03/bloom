# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import constants
from ..tiles import manager


class SpriteGeometry:

    def __init__(
        self,
        scene: core.NodePath,
        tile_manager: manager.Manager
    ):
        self._scene = scene
        self._tile_manager = tile_manager

        self._card_maker = core.CardMaker('geometry')
        self._card_maker.set_frame(0.5, -0.5, 0, 1)

        self._sprites: typing.List[core.NodePath] = []

    def add_facing_sprite(self, name: str, collision_tags: dict, picnum: int, lookup: int, centring: bool, one_sided: bool) -> core.NodePath:
        display = self._new_display(name, picnum, lookup, centring, one_sided)
        display.set_billboard_axis()
        display.set_h(0)

        return display

    def add_directional_sprite(self, name: str, collision_tags: dict, picnum: int, lookup: int, centring: bool, one_sided: bool, theta: float) -> core.NodePath:
        display = self._new_display(name, picnum, lookup, centring, one_sided)
        display.set_h(theta)
        
        return display

    def add_floor_sprite(self, name: str, collision_tags: dict, picnum: int, lookup: int, centring: bool, one_sided: bool, theta: float) -> core.NodePath:
        display = self._new_display(name, picnum, lookup, centring, one_sided)
        display.set_h(theta)
        display.set_p(90)
        
        return display

    def _new_display(self, name: str, picnum: int, lookup: int, centring: bool, one_sided: bool):
        parent_display = self._scene.attach_new_node(name)
        display: core.NodePath = parent_display.attach_new_node(self._card_maker.generate())
        display.set_texture(self._tile_manager.get_tile(picnum, lookup), 1)
        animation_data = self._tile_manager.get_animation_data(picnum)
        if animation_data is not None:
            display.set_name('animated_geometry')
            display.set_python_tag('animation_data', (animation_data, lookup))
        display.set_depth_offset(2, 1)
        display.set_transparency(True)
        display.set_bin('transparent', 1)

        if centring:
            display.set_z(-0.5)
        if not one_sided:
            display.set_two_sided(True)

        return parent_display

