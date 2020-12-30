# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import typing

import yaml
from panda3d import bullet, core

from .. import (audio, cameras, constants, data_loading, edit_mode, editor,
                find_resource, game_map, map_data)
from ..tiles import manager
from ..utils import sky
from . import grid_snapper, sector_geometry, view_clipping
from .map_objects import (EditorSector, EditorSprite, EditorWall,
                          SectorCollection)
from .operations import undo_stack

logger = logging.getLogger(__name__)


class MapEditor:
    _DEFAULT_SKY_INDEX_RANGE = 8

    def __init__(
        self,
        camera_collection: cameras.Cameras,
        map_to_load: game_map.Map,
        audio_manager: audio.Manager,
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
        self._undo_stack = undo_stack.UndoStack(self._camera_collection)

        self._sky_picnum = self._find_sky(map_to_load.sectors)
        self._sky: sky.Sky = None
        self._sky_offsets = map_to_load.sky_offsets
        self._setup_sky_box()

        path = find_resource('sky_indices.yaml')
        with open(path, 'r') as file:
            self._sky_indices = yaml.load(file.read(), Loader=yaml.SafeLoader)

        geometry_factory = sector_geometry.SectorGeometryFactory(
            self._scene,
            self._tile_manager
        )
        self._sectors = SectorCollection(
            map_to_load, 
            audio_manager,
            geometry_factory, 
            self._suggest_sky
        )
        self._sectors.setup_geometry()

        self._last_builder_sector: EditorSector = None
        self._builder_sector: EditorSector = None

    @property
    def scene(self):
        return self._scene
    
    @property
    def undo_stack(self):
        return self._undo_stack

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

    def toggle_view_clipping(self):
        self._clipping_enabled = not self._clipping_enabled

    def invalidate_view_clipping(self):
        self._view_clipping_invalid = True

    def prepare_to_persist(self, builder_position: core.Point3):
        blood_sectors, blood_walls, blood_sprites, builder_sector_index = self._sectors.prepare_to_persist(
            self._find_sector_for_sprite, builder_position
        )
        return self._sky_offsets, blood_sectors, blood_walls, blood_sprites, builder_sector_index

    def to_game_map(self, builder_position: core.Point3):
        sky_offsets, sectors, walls, sprites, builder_sector_index = self.prepare_to_persist(
            builder_position
        )
        map_to_save = game_map.Map()
        map_to_save.sectors[:] = sectors
        map_to_save.walls[:] = walls
        map_to_save.sprites[:] = sprites

        position_x = round(builder_position.x)
        position_y = round(builder_position.y)
        position_z = editor.to_build_height(builder_position.z)
        theta = editor.to_build_angle(self._camera_collection.builder.get_h())
        map_to_save.set_builder_position(
            position_x,
            position_y,
            position_z,
            theta,
            builder_sector_index
        )

        map_to_save.set_sky_offsets(sky_offsets)

        return map_to_save

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

    def _find_sector_for_sprite(self, current_sector: EditorSector, position: core.Point3):
        seen: typing.Set[int] = set()
        last_known_sector = current_sector
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

        return last_known_sector

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
