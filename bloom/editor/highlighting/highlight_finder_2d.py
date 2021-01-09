# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_editor, map_objects, point_sector_finder
from . import highlight_details, sprite_finder_2d, wall_finder_2d


class HighlightFinder2D:
    _VERTEX_OFFSET = 1 / 32

    def __init__(self, editor: map_editor.MapEditor, position: core.Point2, view_scale: core.Vec2):
        self._editor = editor
        self._position = position
        self._view_scale = view_scale.length()
        self._sprite_finder = sprite_finder_2d.SpriteFinder2D(self._position)
        self._wall_finder = wall_finder_2d.WallFinder2D(
            self._position,
            self._view_scale
        )

    def find_highlight(
        self,
        current_highlight: highlight_details.HighlightDetails,
        selected: typing.List[highlight_details.HighlightDetails]
    ):
        selected_highlight = self._highlight_from_selected(selected)
        found_highlight = self._find_highlight(current_highlight)

        if self._highlight_priorty(selected_highlight) >= self._highlight_priorty(found_highlight):
            return selected_highlight
        return found_highlight

    def _find_highlight(self, current_highlight: highlight_details.HighlightDetails):
        if self._editor.builder_sector is None:
            start_sector = self._editor.sectors.sectors[0]
        else:
            start_sector = self._editor.builder_sector

        highlighted_sector = point_sector_finder.PointSectorFinder(
            self._position,
            self._editor.sectors.sectors,
            start_sector
        ).get_new_sector()

        closest_distance = self._vertex_offset
        if highlighted_sector is None:
            closest_highlight: map_objects.EmptyObject = None
            for sector in self._editor.sectors.sectors:
                hit_z = sector.floor_z_at_point(self._position)
                hit = core.Point3(
                    self._position.x,
                    self._position.y,
                    hit_z
                )

                highlight, new_distance = self._find_highlight_in_sector(
                    closest_distance,
                    sector,
                    hit
                )
                if highlight is not None and new_distance < closest_distance:
                    closest_distance = new_distance
                    closest_highlight = highlight

            return closest_highlight

        hit = self._get_hit(highlighted_sector)

        highlight, _ = self._find_highlight_in_sector(
            closest_distance, highlighted_sector, hit
        )
        if highlight is not None:
            return highlight

        return highlight_details.HighlightDetails(
            highlighted_sector,
            map_objects.EditorSector.FLOOR_PART,
            hit
        )

    @staticmethod
    def _highlight_priorty(highlight: highlight_details.HighlightDetails):
        if highlight is None:
            return -1

        if highlight.is_vertex:
            return 3
        if highlight.is_wall:
            return 2
        return 1

    @property
    def _vertex_offset(self):
        return self._VERTEX_OFFSET * self._view_scale

    def _highlight_from_selected(self, selected: typing.List[highlight_details.HighlightDetails]):
        if len(selected) < 1:
            return None

        sectors = [
            selected_object.map_object
            for selected_object in selected
            if selected_object.is_sector
        ]
        highlighted_sector: map_objects.EditorSector = None
        for sector in sectors:
            if sector.point_in_sector(self._position):
                highlighted_sector = sector
                break

        if highlighted_sector is None:
            hit = selected[0].hit_position
        else:
            hit = self._get_hit(highlighted_sector)

        sprites = [
            selected_object.map_object
            for selected_object in selected
            if selected_object.is_sprite
        ]
        highlight, _ = self._closest_sprite_highlight(hit, sprites)
        if highlight is not None:
            return highlight

        walls = [
            selected_object.map_object
            for selected_object in selected
            if selected_object.is_wall
        ]

        highlight, _ = self._closest_vertex_highlight(hit, walls)
        if highlight is not None:
            return highlight

        highlight, _ = self._closest_wall_highlight(hit, walls)
        if highlight is not None:
            return highlight

        if highlighted_sector is not None:
            return highlight_details.HighlightDetails(
                highlighted_sector,
                map_objects.EditorSector.FLOOR_PART,
                hit
            )

        return None

    def _get_hit(self, sector: map_objects.EditorSector):
        hit_z = sector.floor_z_at_point(self._position)
        return core.Point3(
            self._position.x,
            self._position.y,
            hit_z
        )

    def _find_highlight_in_sector(self, closest_distance: float, sector: map_objects.EditorSector, hit: core.Point3):
        highlight, distance = self._closest_sprite_highlight(hit, sector.sprites)
        if highlight is not None:
            return highlight, distance

        highlight, distance = self._closest_vertex_highlight(hit, sector.walls)
        if highlight is not None:
            return highlight, distance

        highlight, distance = self._closest_wall_highlight(hit, sector.walls)
        if highlight is not None:
            return highlight, distance

        return None, closest_distance

    def _closest_sprite_highlight(self, hit: core.Point3, sprites: typing.List[map_objects.EditorSprite]):
        closest_sprite, distance = self._sprite_finder.closest_sprite(sprites)
        if closest_sprite is not None:
            return highlight_details.HighlightDetails(
                closest_sprite,
                closest_sprite.default_part,
                hit
            ), distance
        return None, None

    def _closest_vertex_highlight(self, hit: core.Point3, walls: typing.List[map_objects.EditorWall]):
        vertex, distance = self._wall_finder.closest_vertex(walls)
        if vertex is not None:
            return highlight_details.HighlightDetails(
                vertex,
                f'{vertex.vertex_part_name}_highlight',
                hit
            ), distance
        return None, None

    def _closest_wall_highlight(self, hit: core.Point3, walls: typing.List[map_objects.EditorWall]):
        wall, distance = self._wall_finder.closest_wall(walls)
        if wall is not None:
            return highlight_details.HighlightDetails(
                wall,
                wall.default_part,
                hit
            ), distance
        return None, None
