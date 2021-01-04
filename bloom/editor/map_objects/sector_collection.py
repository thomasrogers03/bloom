# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import bullet, core

from ... import audio, constants, editor, game_map, map_data
from .. import (event_grouping, marker_constants, plane, ror_constants,
                sector_geometry, sprite_find_sector, undo_stack)
from . import empty_object, geometry_highlight, sprite, wall
from .drawing import sector as drawing_sector
from .sector import EditorSector


class SectorCollection:

    def __init__(
        self,
        map_to_load: game_map.Map,
        audio_manager: audio.Manager,
        geometry_factory: sector_geometry.SectorGeometryFactory,
        suggest_sky_picnum: typing.Callable[[int], int],
        undos: undo_stack.UndoStack
    ):
        self._audio_manager = audio_manager
        self._geometry_factory = geometry_factory
        self._suggest_sky_picnum = suggest_sky_picnum
        self._event_groupings = event_grouping.EventGroupingCollection()
        self._undo_stack = undos

        self._sectors: typing.List[EditorSector] = []
        sprite_mapping: typing.Dict[int, sprite.EditorSprite] = {}
        marker_sprite_mapping: typing.Dict[int, sprite.EditorSprite] = {}
        for sector_index, map_sector in enumerate(map_to_load.sectors):
            self.new_sector(map_sector).load(
                map_to_load,
                sector_index,
                sprite_mapping,
                marker_sprite_mapping
            )

        lower_sectors: typing.Dict[int, EditorSector] = {}
        upper_sectors: typing.Dict[int, EditorSector] = {}
        for blood_sprite in map_to_load.sprites:
            if blood_sprite.sprite.tags[0] in ror_constants.LOWER_LINK_TYPES:
                lower_sectors[blood_sprite.data.data1] = self._sectors[blood_sprite.sprite.sector_index]
            elif blood_sprite.sprite.tags[0] in ror_constants.UPPER_LINK_TYPES:
                upper_sectors[blood_sprite.data.data1] = self._sectors[blood_sprite.sprite.sector_index]

        all_objects: typing.List[empty_object.EmptyObject] = []
        for editor_sector in self._sectors:
            editor_sector.setup_walls_and_sprites_after_load(
                self._sectors,
                map_to_load,
                lower_sectors,
                upper_sectors,
                sprite_mapping,
                marker_sprite_mapping,
            )
            all_objects.append(editor_sector)
            for editor_wall in editor_sector.walls:
                all_objects.append(editor_wall)
            for editor_sprite in editor_sector.sprites:
                all_objects.append(editor_sprite)

        self._event_groupings.load(all_objects)

    @property
    def sectors(self) -> typing.List[EditorSector]:
        return self._sectors

    @property
    def event_groupings(self):
        return self._event_groupings
    
    @property
    def undos(self):
        return self._undo_stack

    def destroy_sector(self, sector_to_destroy: EditorSector):
        sector_to_destroy.destroy()
        self.sectors.remove(sector_to_destroy)

    def create_sector(self, template: EditorSector):
        new_build_sector = template.sector.sector.copy()
        new_build_sector.tags[0] = 0
        new_blood_sector = map_data.sector.Sector(
            sector=new_build_sector,
            data=map_data.sector.BloodSectorData()
        )

        new_sector = self.new_sector(new_blood_sector)
        new_sector.setup_geometry()

        return new_sector

    def create_empty_sector(self):
        new_sector = self.new_sector(map_data.sector.Sector())
        new_sector.setup_geometry()

        return new_sector

    def new_sector(self, blood_sector: game_map.sector.Sector):
        index = len(self._sectors)

        new_sector = EditorSector(
            blood_sector,
            str(index),
            self._audio_manager,
            self._geometry_factory,
            self._suggest_sky_picnum,
            self._undo_stack
        )

        def _undo():
            self.destroy_sector(new_sector)
    
        def _redo():
            new_sector.undestroy()
            self._sectors.append(new_sector)

        operation = undo_stack.SimpleUndoableOperation(
            'Add Sector',
            _undo,
            _redo
        )
        operation.apply()
        self._undo_stack.add_operation(operation)

        return new_sector

    def setup_geometry(self):
        for sector in self._sectors:
            sector.setup_geometry()

    def prepare_to_persist(
        self,
        find_sector: typing.Callable[['editor.sector.EditorSector', core.Point3], 'editor.sector.EditorSector'],
        builder_position: core.Point3
    ):
        blood_sectors: typing.List[map_data.sector.Sector] = []
        blood_walls: typing.List[map_data.wall.Wall] = []
        blood_sprites: typing.List[map_data.sprite.Sprite] = []

        sector_index_mapping: typing.Dict[EditorSector, int] = {}
        wall_index_mapping: typing.Dict[wall.EditorWall, int] = {}
        sprite_index_mapping: typing.Dict[sprite.EditorSprite, int] = {}
        marker_id = marker_constants.START_ID

        self._event_groupings.prepare_to_persist()

        for sector_index, editor_sector in enumerate(self._sectors):
            sector_index_mapping[editor_sector] = sector_index
            for editor_wall in editor_sector.walls:
                wall_index_mapping[editor_wall] = len(wall_index_mapping)
            for editor_sprite in editor_sector.sprites:
                sprite_index_mapping[editor_sprite] = len(sprite_index_mapping)
            for editor_sprite in editor_sector.markers:
                if editor_sprite is not None:
                    editor_sprite.sprite.sprite.velocity_x = marker_id
                    sprite_index_mapping[editor_sprite] = len(sprite_index_mapping)
                    marker_id += 1

        for editor_sector in self._sectors:
            for editor_wall in editor_sector.walls:
                blood_wall = editor_wall.prepare_to_persist(
                    sector_index_mapping,
                    wall_index_mapping
                )
                blood_walls.append(blood_wall)

            for editor_sprite in editor_sector.sprites:
                sprite_find_sector.SpriteFindSector(editor_sprite, self._sectors).update_sector()
                blood_sprite = editor_sprite.prepare_to_persist(sector_index_mapping)
                blood_sprites.append(blood_sprite)

            markers = [-1, -1]
            for marker_index, editor_marker in enumerate(editor_sector.markers):
                if editor_marker is not None:
                    blood_sprite = editor_marker.prepare_to_persist(sector_index_mapping)
                    markers[marker_index] = blood_sprite.sprite.velocity_x
                    blood_sprites.append(blood_sprite)

            blood_sector = editor_sector.prepare_to_persist(wall_index_mapping)
            blood_sector.data.markers = markers
            blood_sectors.append(blood_sector)

        builder_sector = find_sector(None, builder_position)
        if builder_sector is not None:
            builder_sector_index = sector_index_mapping[builder_sector]
        else:
            builder_sector_index = -1

        return blood_sectors, blood_walls, blood_sprites, builder_sector_index
