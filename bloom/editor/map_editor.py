# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import math
import typing

import yaml
from panda3d import bullet, core

from .. import (cameras, constants, data_loading, edit_mode, editor, game_map,
                map_data)
from ..tiles import manager
from ..utils import sky
from . import grid_snapper, sector_geometry, view_clipping
from .map_objects.sector import EditorSector, SectorCollection
from .map_objects.sprite import EditorSprite
from .map_objects.wall import EditorWall

logger = logging.getLogger(__name__)


class MapEditor:
    _DEFAULT_SKY_INDEX_RANGE = 8

    def __init__(
        self,
        camera_collection: cameras.Cameras,
        map_to_load: game_map.Map,
        tile_manager: manager.Manager
    ):
        logger.info('Setting up sector editor')

        self._camera_collection = camera_collection
        self._scene: core.NodePath = self._camera_collection.scene.attach_new_node(
            '3d_view'
        )
        self._tile_manager = tile_manager
        self._texture_stage = core.TextureStage.get_default()
        self._last_hit_position = core.Vec3()
        self._ticks = 0
        self._snapper = grid_snapper.GridSnapper()
        self._clipping_debug: core.NodePath = None
        self._clipping_enabled = constants.PORTALS_ENABLED
        self._view_clipping_invalid = True

        hit_debug_segs = core.LineSegs('hit')
        hit_debug_segs.set_thickness(4)
        hit_debug_segs.draw_to(-0.5, -0.5, 0)
        hit_debug_segs.draw_to(-0.5, 0.5, 0)
        hit_debug_segs.draw_to(0.5, 0.5, 0)
        hit_debug_segs.draw_to(0.5, -0.5, 0)
        hit_debug_segs.draw_to(-0.5, -0.5, 0)
        hit_debug_node = hit_debug_segs.create()
        self._hit_debug: core.NodePath = self._scene.attach_new_node(
            hit_debug_node
        )
        self._hit_debug.set_scale(1024)
        self._hit_debug.set_depth_offset(constants.HIGHLIGHT_DEPTH_OFFSET, 1)
        self._hit_debug.hide()

        self._tx_rx_debug: core.NodePath = None

        self._sky_picnum = self._find_sky(map_to_load.sectors)
        self._sky: sky.Sky = None
        self._sky_offsets = map_to_load.sky_offsets
        self._setup_sky_box()

        with open('bloom/resources/sky_indices.yaml', 'r') as file:
            self._sky_indices = yaml.load(file.read(), Loader=yaml.SafeLoader)

        split_segment = core.LineSegs('splitter')
        split_segment.set_thickness(4)
        split_segment.draw_to(0, 0, 0)
        split_segment.draw_to(0, 0, 1)
        split_segment_node = split_segment.create()
        self._splitter_display: core.NodePath = self._scene.attach_new_node(
            split_segment_node
        )
        self._splitter_display.set_depth_offset(2 * constants.HIGHLIGHT_DEPTH_OFFSET, 1)
        self._splitter_display.hide()

        geometry_factory = sector_geometry.SectorGeometryFactory(
            self._scene,
            self._tile_manager
        )
        self._sectors = SectorCollection(map_to_load, geometry_factory, self._suggest_sky)
        self._sectors.setup_geometry()

        self._last_builder_sector: EditorSector = None
        self._builder_sector: EditorSector = None

    @property
    def scene(self):
        return self._scene

    def unload(self):
        self._scene.remove_node()
        self._scene = None

    @staticmethod
    def _find_sky(sectors: typing.List[map_data.sector.Sector]):
        for sector in sectors:
            if sector.sector.floor_stat.parallax:
                return sector.sector.floor_picnum
            if sector.sector.ceiling_stat.parallax:
                return sector.sector.ceiling_picnum
        return None

    @property
    def builder_sector(self):
        return self._builder_sector

    def _suggest_sky(self, suggested_picnum: int):
        if self._sky_picnum is None:
            self._sky_picnum = suggested_picnum
            sky_range = self._sky_indices.get(
                self._sky_picnum, 
                self._DEFAULT_SKY_INDEX_RANGE
            )
            self._sky_offsets = list(range(sky_range))
            self._setup_sky_box()
        return self._sky_picnum

    def _setup_sky_box(self):
        if self._sky_picnum is not None:
            self._sky = sky.Sky(
                self._camera_collection,
                self._tile_manager,
                self._sky_picnum,
                self._sky_offsets
            )

    def update_builder_sector(self, builder_position: core.Vec3, force=False):
        self.invalidate_view_clipping()

        seen: typing.Set[int] = set()
        if force:
            self._builder_sector = None
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

        for editor_sector in self._sectors.sectors:
            self._builder_sector = self._find_sector_through_portals(
                editor_sector,
                seen,
                builder_position,
                1000
            )
            if self._builder_sector is not None:
                return

        self._builder_sector = self._last_builder_sector

    @property
    def snapper(self):
        return self._snapper

    @property
    def sectors(self):
        return self._sectors

    def find_unused_sprite_data_1(self):
        found: typing.Set[int] = set()

        for editor_sector in self._sectors.sectors:
            for editor_sprite in editor_sector.sprites:
                found.add(editor_sprite.sprite.data.data1)

        for value in range(65535):
            if value not in found:
                return value
    
        raise Exception('Ran out of sprite data 1!')

    def update_for_frame(self):
        for sector in self._sectors.sectors:
            sector.reset_geometry_if_necessary()

        if self._view_clipping_invalid:
            self._show_traceable_sectors()
            self._view_clipping_invalid = False

    @property
    def ticks(self):
        return self._ticks

    def tick(self):
        self._ticks += 1

        for sector in self._sectors.sectors:
            if sector.is_hidden:
                continue

            geometry = sector.get_animated_geometry()
            for node_path in geometry:
                animation_data_and_lookup = node_path.get_python_tag('animation_data')
                animation_data: manager.AnimationData = animation_data_and_lookup[0]
                
                lookup: int = animation_data_and_lookup[1]
                offset = (self._ticks // animation_data.ticks_per_frame) % animation_data.count
                new_picnum = animation_data.picnum + offset

                node_path.set_texture(self._tile_manager.get_tile(new_picnum, lookup))

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

        for editor_sector in self._sectors.sectors:
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

    def toggle_view_clipping(self):
        self._clipping_enabled = not self._clipping_enabled

    def invalidate_view_clipping(self):
        self._view_clipping_invalid = True

    def _show_traceable_sectors(self):
        if not self._clipping_enabled or self._scene is None:
            return

        if self._clipping_debug is not None:
            self._clipping_debug.remove_node()
            self._clipping_debug = None

        if self._builder_sector is not None:
            self._clipping_debug = self._scene.attach_new_node('clipping_debug')
            clipper = view_clipping.ViewClipping(
                self._builder_sector, 
                self._camera_collection, 
                self._clipping_debug
            )
            clipper.clip()
            for editor_sector in self._sectors.sectors:
                if editor_sector in clipper.visible_sectors:
                    editor_sector.show()
                else:
                    editor_sector.hide()

    def prepare_to_persist(self, builder_position: core.Point3):
        blood_sectors, blood_walls, blood_sprites, builder_sector_index = EditorSector.prepare_to_persist(
            self._find_sector_for_sprite, self._sectors.sectors, builder_position
        )
        return self._sky_offsets, blood_sectors, blood_walls, blood_sprites, builder_sector_index
