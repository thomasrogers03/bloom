# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import math
import typing

from panda3d import bullet, core

from .. import constants, data_loading, edit_mode, editor, game_map, map_data
from ..utils import sky
from . import (grid_snapper, highlight, sector_selector, sprite_selector,
               wall_bunch, wall_selector)
from .sector import EditorSector
from .sprite import EditorSprite
from .wall import EditorWall

logger = logging.getLogger(__name__)


class MapEditor:

    def __init__(
        self,
        render: core.NodePath,
        render2d: core.NodePath,
        scene: core.NodePath,
        map_to_load: game_map.Map,
        get_tile_callback: typing.Callable[[int], core.Texture],
        collision_world: bullet.BulletWorld
    ):
        logger.info('Setting up sector editor')

        self._render = render
        self._scene = scene
        self._get_tile_callback = get_tile_callback
        self._texture_stage = core.TextureStage.get_default()
        self._collision_world = collision_world
        self._highlight: highlight.Highlight = None
        self._selection: highlight.Highlight = None
        self._last_hit_position = core.Vec3()
        self._selected_is_highlighted = False
        self._ticks = 0
        self._snapper = grid_snapper.GridSnapper()

        self._sky = sky.Sky(
            render2d,
            get_tile_callback,
            self._find_sky(map_to_load.sectors),
            map_to_load.sky_offsets
        )

        split_segment = core.LineSegs('splitter')
        split_segment.set_thickness(4)
        split_segment.draw_to(core.Vec3(0, 0, 0))
        split_segment.draw_to(core.Vec3(0, 0, 1))
        split_segment_node = split_segment.create()
        self._splitter_display: core.NodePath = self._scene.attach_new_node(
            split_segment_node)
        self._splitter_display.set_depth_offset(2, 1)
        self._splitter_display.hide()

        self._sectors = [
            EditorSector(map_to_load.sectors[sector_index]).load(
                sector_index, map_to_load)
            for sector_index in range(len(map_to_load.sectors))
        ]
        self._last_builder_sector: EditorSector = None
        self._builder_sector: EditorSector = None

        for sector in self._sectors:
            sector.setup_walls_and_sprites_after_load(self._sectors, map_to_load)

        self._vertex_format = self._create_vertex_format()

        for sector_index, sector in enumerate(self._sectors):
            sector.setup_for_rendering(
                self._scene,
                str(sector_index),
                self._vertex_format,
                self._get_tile_callback
            )
            sector.setup_geometry(self._collision_world)

    @staticmethod
    def _create_vertex_format():
        vertex_array_format = core.GeomVertexArrayFormat()
        vertex_array_format.add_column(
            'vertex',
            3,
            core.Geom.NT_float32,
            core.Geom.C_point
        )
        vertex_array_format.add_column(
            'texcoord',
            2,
            core.Geom.NT_float32,
            core.Geom.C_texcoord
        )

        vertex_format = core.GeomVertexFormat()
        vertex_format.add_array(vertex_array_format)

        return core.GeomVertexFormat.register_format(vertex_format)

    @staticmethod
    def _find_sky(sectors: typing.List[map_data.sector.Sector]):
        for sector in sectors:
            if sector.sector.floor_stat.parallax:
                return sector.sector.floor_picnum
            if sector.sector.ceiling_stat.parallax:
                return sector.sector.ceiling_picnum
        return 0

    def attach_display_node_to_sector(self, sector_index: int, node: typing.Union[str, core.PandaNode]):
        return self._sectors[sector_index].attach_display_node(node)

    def update_builder_sector(self, builder_position: core.Vec3):
        seen: typing.Set[int] = set()
        self._last_builder_sector = self._builder_sector
        if self._builder_sector is not None:
            self._builder_sector = self._find_sector_through_portals(
                self._builder_sector,
                seen,
                builder_position,
                10
            )
            if self._builder_sector is not None:
                return

        for editor_sector in self._sectors:
            self._builder_sector = self._find_sector_through_portals(
                editor_sector,
                seen,
                builder_position,
                1000
            )
            if self._builder_sector is not None:
                return

        self._builder_sector = None

    def perform_select(self):
        if self._selection is not None:
            self._selection.remove()
        self._selection = self._highlight
        if self._selection is not None:
            self._selection.colour = core.Vec3(0.125, 0.125, 1)
            self._selected_is_highlighted = True

    def selected_is_highlighted(self):
        return self._selected_is_highlighted

    def highlight_mouse_hit(self, start: core.TransformState, end: core.TransformState):
        found_highlight: highlight.Highlight = self._highlight

        shape = bullet.BulletSphereShape(0.5)
        result: bullet.BulletClosestHitSweepResult = self._collision_world.sweep_test_closest(
            shape,
            start,
            end,
            core.BitMask32.all_on()
        )

        if result is not None:
            node: bullet.BulletRigidBodyNode = result.get_node()
            if node is not None:
                tags: dict = node.get_python_tags()
                part = node.get_name()

                if 'direction' in tags:
                    direction: core.Vec3 = tags['direction']
                    dot = direction.dot(result.get_hit_normal())
                    if dot > 0:
                        if self._highlight is not None:
                            self._highlight.remove()
                            self._highlight = None
                        return

                position = result.get_hit_pos()
                position = self._scene.get_relative_point(self._render, position)
                self._last_hit_position = position

                self._splitter_display.hide()
                if 'sector' in tags:
                    item: EditorSector = tags['sector']
                    selector_type = sector_selector.Selector
                elif 'wall' in tags:
                    item: EditorWall = tags['wall']
                    selector_type = wall_selector.Selector

                    position_2d = core.Point2(
                        position.x, 
                        position.y
                    ) - item.get_normal() * 10

                    bottom = item.sector.floor_z_at_point(
                        core.Point2(position.x, position.y))
                    top = item.sector.ceiling_z_at_point(
                        core.Point2(position.x, position.y))
                    self._splitter_display.set_pos(position_2d.x, position_2d.y, top)
                    self._splitter_display.set_sz(bottom - top)
                    self._splitter_display.show()
                else:
                    item: EditorSprite = tags['sprite']
                    selector_type = sprite_selector.Selector
                item.show_debug()
                selector = selector_type(self._scene, item, part, self._snapper)

                found_highlight = highlight.Highlight(
                    core.Vec3(1, 1, 0.125),
                    item,
                    part,
                    selector
                )

        if found_highlight != self._highlight:
            if self._highlight is not None:
                self._highlight.remove()

            if found_highlight == self._selection:
                self._selected_is_highlighted = True
            else:
                self._selected_is_highlighted = False
                self._highlight = found_highlight

    @property
    def snapper(self):
        return self._snapper

    @property
    def sectors(self):
        return self._sectors

    def get_selected_picnum(self):
        if self._selection is None:
            return -1

        return self._selection.selector.get_picnum()

    def set_selected_picnum(self, picnum: int):
        if self._selection is None:
            return

        self._selection.selector.set_picnum(picnum)

    def move_selection(
        self,
        total_delta: core.Vec2,
        delta: core.Vec2,
        total_camera_delta: core.Vec2,
        camera_delta: core.Vec2,
        modified: bool
    ):
        if self._selection is None or not self._selected_is_highlighted:
            return

        self._splitter_display.hide()
        self._selection.selector.begin_move(self._last_hit_position)
        self._selection.selector.move(
            total_delta,
            delta,
            total_camera_delta,
            camera_delta,
            modified
        )

    def end_move_selection(self):
        if self._selection is None:
            return

        self._selection.selector.end_move()

    def split_highlight(self, modified: bool):
        if self._selected_is_highlighted:
            highlight = self._selection
        else:
            highlight = self._highlight

        if highlight is None:
            return

        highlight.selector.split(self._last_hit_position, self._sectors, modified)

    def get_selector(self):
        if self._selection is None:
            return None

        return self._selection.selector

    def get_selected_and_last_hit_position(self):
        if self._selection is None:
            return None, None

        return self._selection.selector.get_selected(), self._last_hit_position

    def tick(self):
        for sector in self._sectors:
            sector.reset_geometry_if_necessary()

        self._ticks += 1
        if self._highlight is not None:
            self._highlight.tick(self._ticks)
        if self._selection is not None:
            self._selection.tick(self._ticks)

    def _find_sector_for_sprite(self, current_sector: EditorSector, position: core.Point3):
        seen: typing.Set[int] = set()
        if current_sector is not None:
            current_sector = self._find_sector_through_portals(
                current_sector,
                seen,
                position,
                10
            )
            if current_sector is not None:
                return current_sector

        for editor_sector in self._sectors:
            current_sector = self._find_sector_through_portals(
                editor_sector,
                seen,
                position,
                1000
            )
            if current_sector is not None:
                return current_sector

        return None

    def _find_sector_through_portals(
        self,
        current_sector: EditorSector,
        seen: typing.Set[EditorSector],
        position: core.Vec3,
        depth_left
    ):
        if current_sector in seen or depth_left < 1:
            return None

        seen.add(current_sector)
        if current_sector.vector_in_sector(position):
            return current_sector

        for adjacent_sector in current_sector.adjacent_sectors():
            found_sector = self._find_sector_through_portals(
                adjacent_sector,
                seen,
                position,
                depth_left - 1
            )
            if found_sector is not None:
                return found_sector

        return None

    def hide_sectors(self):
        if not constants.PORTALS_ENABLED:
            return

        for editor_sector in self._sectors:
            editor_sector.hide()

    def show_traceable_sectors(self, project_point: typing.Callable[[core.Vec2], core.Point3]):
        if not constants.PORTALS_ENABLED:
            return

        if self._builder_sector is not None:
            seen = set()
            clip_buffer = [0.0] * 2048
            self._show_traceable_sectors(
                project_point,
                self._builder_sector,
                seen
            )
        else:
            for editor_sector in self._sectors:
                editor_sector.show()

    @staticmethod
    def _cleanup_polygon(polygon: typing.List[core.Vec2]):
        original_length = len(polygon)
        point_count = len(polygon)
        index = 0
        while index < point_count:
            index_p2 = (index + 1) % point_count
            index_p3 = (index + 2) % point_count

            point_1 = polygon[index]
            point_2 = polygon[index_p2]
            point_3 = polygon[index_p3]

            direction_1 = point_2 - point_1
            direction_2 = point_3 - point_2

            if direction_1.x == 0 and direction_2.x == 0 and (direction_1.y * direction_2.y) < 0:
                del polygon[index_p2]
                point_count -= 1
            elif direction_1.y == 0 and direction_2.y == 0 and (direction_1.x * direction_2.x) < 0:
                del polygon[index_p2]
                point_count -= 1
            else:
                index += 1
        if point_count != original_length:
            logger.debug('Found sector with connecting walls having angle 0')

    def _show_traceable_sectors(
        self,
        project_point: typing.Callable[[core.Vec2], core.Point3],
        current_sector: EditorSector,
        seen: typing.Set[EditorSector],
        min_x=-1,
        max_x=1,
        max_z=1,
        depth_left=100,
    ):
        if depth_left < 1:
            return

        seen.add(current_sector)
        current_sector.show()

        seen_walls: typing.Set(EditorWall) = set()
        bunches: typing.List[wall_bunch.WallBunch] = []

        portals = list(current_sector.portal_walls())
        for portal in portals:
            if portal in seen_walls or portal.other_side_sector in seen:
                continue

            bunch = wall_bunch.WallBunch(portal, project_point)

            previous_wall = portal.wall_previous_point
            while bunch.add_wall_previous(previous_wall):
                seen_walls.add(previous_wall)
                previous_wall = previous_wall.wall_previous_point

            next_wall = portal.wall_point_2
            while bunch.add_wall_next(next_wall):
                seen_walls.add(next_wall)
                next_wall = next_wall.wall_point_2

            bunches.append(bunch)

        for bunch in bunches:
            portal, other_side_sector = bunch.make_portal(min_x, max_x, max_z)
            if portal is not None:
                self._show_traceable_sectors(
                    project_point,
                    other_side_sector,
                    seen,
                    portal.x,
                    portal.y,
                    portal.z,
                    depth_left - 1
                )

    def prepare_to_persist(self, builder_position: core.Point3):
        return EditorSector.prepare_to_persist(self._find_sector_for_sprite, self._sectors, builder_position)
