# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import bullet, core

from .. import constants
from ..tiles import manager
from . import sprite_geometry


class GeometryPart:

    def __init__(self, picnum: int, lookup: int, pannable: bool, part: str):
        self.picnum = picnum
        self.lookup = lookup
        self.pannable = pannable
        self.part = part
        self.node: core.PandaNode = None

    @property
    def is_floor(self):
        return self.part == 'floor'

    @property
    def is_ceiling(self):
        return self.part == 'ceiling'


class SectorGeometry:

    def __init__(
        self,
        scene: core.NodePath,
        name: str,
        tile_manager: manager.Manager
    ):
        self._scene = scene
        self._name = name

        self._nodes: typing.Dict[int, typing.Dict[int, core.GeomNode]] = {}
        self._pannable_nodes: typing.List[core.GeomNode] = []
        self._tile_manager = tile_manager
        self._node_2d = core.GeomNode(f'{self._name}_2d')

        self._display: core.NodePath = self._scene.attach_new_node(self._name)
        self._display.set_bin('opaque', 2)
        self._display.set_transparency(True)

        self._sprite_geometry = sprite_geometry.SpriteGeometry(
            self._display,
            self._tile_manager
        )

        display_2d: core.NodePath = self._display.attach_new_node(self._node_2d)
        display_2d.hide(constants.SCENE_3D)
        display_2d.set_depth_offset(constants.DEPTH_OFFSET, 1)

        self._2d_segments = core.LineSegs('2d')

    @property
    def sprite_geometry(self):
        return self._sprite_geometry

    @property
    def scene(self):
        return self._scene

    @property
    def display(self):
        return self._display

    def add_2d_geometry(self, point_1: core.Point2, point_2: core.Point2, colour: core.Vec4, thickness: float):
        if not constants.PORTALS_DEBUGGING_ENABLED:
            self._add_2d_segments(self._2d_segments, point_1,
                                  point_2, colour, thickness=thickness)
            self._add_2d_vertex_segments(self._2d_segments, point_1, colour)

    def add_2d_highlight_geometry(self, name: str, point_1: core.Point2, point_2: core.Point2):
        segments = self._create_2d_segments(
            point_1, point_2, core.Vec4(1, 1, 1, 1), thickness=4, z_offset=-512)
        highlight_display_node = segments.create(dynamic=False)
        highlight_display: core.NodePath = self._display.attach_new_node(
            highlight_display_node)
        highlight_display.set_name(name)
        self._setup_highlight_display(highlight_display)
        highlight_display.hide()

        return highlight_display

    def add_geometry(self, geometry: core.Geom, part: GeometryPart):
        if part.pannable:
            node = core.GeomNode(f'pannable_geometry_{len(self._pannable_nodes)}')
            node.add_geom(geometry)
            node.set_python_tag('picnum', part.picnum)
            node.set_python_tag('lookup', part.lookup)
            self._pannable_nodes.append(node)
        else:
            node = self._get_node_for_picnum(part.picnum, part.lookup)
            node.add_geom(geometry)
        part.node = node

    def add_vertex_highlight_geometry(self, point: core.Point2, bottom: float, top: float, part: str):
        point_1 = core.Point3(point.x, point.y, bottom)
        point_2 = core.Point3(point.x, point.y, top)

        highlight_display_node = core.GeomNode(f'{part}_highlight')

        segments = self._create_3d_segments(point_1, point_2, core.Vec4(1, 1, 1, 1))
        self._add_2d_vertex_segments(segments, point_1, core.Vec4(1, 1, 1, 1))
        segments.create(highlight_display_node, dynamic=False)

        highlight_display: core.NodePath = self._display.attach_new_node(
            highlight_display_node)
        self._setup_highlight_display(highlight_display)
        highlight_display.set_depth_test(False)
        highlight_display.hide()

        return highlight_display

    def add_highlight_geometry(self, geometry: core.Geom, part: str):
        highlight_display_node = core.GeomNode(f'{part}_highlight')
        highlight_display_node.add_geom(geometry)
        highlight_display: core.NodePath = self._display.attach_new_node(
            highlight_display_node)
        self._setup_highlight_display(highlight_display)
        highlight_display.set_color(1, 1, 1, 0.25)
        highlight_display.hide()

        return highlight_display

    def get_tile_dimensions(self, picnum: int):
        return self._tile_manager.get_tile_dimensions(picnum)

    def build(self):
        for lookup, nodes in self._nodes.items():
            for picnum, node in nodes.items():
                sector_shape: core.NodePath = self._display.attach_new_node(node)
                sector_shape.set_texture(self._tile_manager.get_tile(picnum, lookup), 1)
                animation_data = self._tile_manager.get_animation_data(picnum)
                if animation_data is not None:
                    sector_shape.set_name(f'animated_geometry_{lookup}_{picnum}')
                    sector_shape.set_python_tag(
                        'animation_data', (animation_data, lookup))

        for node in self._pannable_nodes:
            picnum = node.get_python_tag('picnum')
            lookup = node.get_python_tag('lookup')

            sector_shape: core.NodePath = self._display.attach_new_node(node)
            sector_shape.set_texture(self._tile_manager.get_tile(picnum, lookup), 1)

        self._2d_segments.create(self._node_2d, dynamic=False)

        return self._display

    @staticmethod
    def _create_2d_vertex_segments(point: core.Point2, colour: core.Vec4):
        segments = core.LineSegs('2d_vertex')
        SectorGeometry._add_2d_vertex_segments(segments, point, colour)
        return segments

    @staticmethod
    def _add_2d_vertex_segments(segments: core.LineSegs, point: core.Point2, colour: core.Vec4):
        segments.set_thickness(2)
        segments.set_color(colour)
        segments.move_to(point.x - 32, point.y - 32, -constants.REALLY_BIG_NUMBER)
        segments.draw_to(point.x - 32, point.y + 32, -constants.REALLY_BIG_NUMBER)
        segments.draw_to(point.x + 32, point.y + 32, -constants.REALLY_BIG_NUMBER)
        segments.draw_to(point.x + 32, point.y - 32, -constants.REALLY_BIG_NUMBER)
        segments.draw_to(point.x - 32, point.y - 32, -constants.REALLY_BIG_NUMBER)

    def _setup_highlight_display(self, highlight: core.NodePath):
        highlight.set_two_sided(True)
        highlight.set_texture_off(1)
        highlight.set_depth_offset(constants.HIGHLIGHT_DEPTH_OFFSET, 1)
        highlight.set_bin('fixed', constants.FRONT_MOST)

        highlight.set_python_tag('is_geometry', True)

    def _create_3d_segments(self, point_1: core.Point3, point_2: core.Point3, colour: core.Vec4):
        segments = core.LineSegs('3d')
        segments.set_thickness(8)
        segments.set_color(colour)
        segments.draw_to(point_1)
        segments.draw_to(point_2)

        return segments

    @staticmethod
    def _create_2d_segments(point_1: core.Point2, point_2: core.Point2, colour: core.Vec4, thickness=2, z_offset=0):
        segments = core.LineSegs('2d')
        SectorGeometry._add_2d_segments(
            segments, point_1, point_2, colour, thickness=thickness, z_offset=z_offset)
        return segments

    @staticmethod
    def _add_2d_segments(
        segments: core.LineSegs,
        point_1: core.Point2,
        point_2: core.Point2,
        colour: core.Vec4,
        thickness=2,
        z_offset=0
    ):
        segments.set_thickness(thickness)
        segments.set_color(colour)
        segments.move_to(point_1.x, point_1.y, -constants.REALLY_BIG_NUMBER + z_offset)
        segments.draw_to(point_2.x, point_2.y, -constants.REALLY_BIG_NUMBER + z_offset)

    def _get_node_for_picnum(self, picnum: int, lookup: int):
        if lookup not in self._nodes:
            self._nodes[lookup] = {}

        lookup_nodes = self._nodes[lookup]
        if picnum not in lookup_nodes:
            lookup_nodes[picnum] = core.GeomNode('geometry')

        return lookup_nodes[picnum]

    def destroy(self):
        self._display.remove_node()


class SectorGeometryFactory:

    def __init__(
        self,
        scene: core.NodePath,
        tile_manager: manager.Manager
    ):
        self._scene = scene
        self._tile_manager = tile_manager

    @property
    def tile_manager(self):
        return self._tile_manager

    def new_geometry(self, name: str):
        return SectorGeometry(self._scene, name, self._tile_manager)

    def remove_geometry(self, display: core.NodePath):
        if display is None:
            return

        display.remove_node()
