# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from .. import map_editor, map_objects, point_sector_finder
from . import highlight_details, sprite_finder_2d, wall_finder_2d


class HighlightFinder2D:
    _VERTEX_OFFSET = 1 / 32

    def __init__(self, editor: map_editor.MapEditor, position: core.Point2, view_scale: core.Vec2):
        self._editor = editor
        self._position = position
        self._view_scale = view_scale.length()

    def find_highlight(self, current_highlight: highlight_details.HighlightDetails):
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

        hit_z = highlighted_sector.floor_z_at_point(self._position)
        hit = core.Point3(
            self._position.x,
            self._position.y,
            hit_z
        )

        highlight, _ = self._find_highlight_in_sector(
            closest_distance, highlighted_sector, hit)
        if highlight is not None:
            return highlight

        return highlight_details.HighlightDetails(
            highlighted_sector,
            map_objects.EditorSector.FLOOR_PART,
            hit
        )

    @property
    def _vertex_offset(self):
        return self._VERTEX_OFFSET * self._view_scale

    def _find_highlight_in_sector(self, closest_distance: float, sector: map_objects.EditorSector, hit: core.Point3):
        closest_sprite, distance = sprite_finder_2d.SpriteFinder2D(
            sector,
            self._position
        ).closest_sprite()
        if closest_sprite is not None:
            return highlight_details.HighlightDetails(
                closest_sprite,
                closest_sprite.default_part,
                hit
            ), distance

        wall_finder = wall_finder_2d.WallFinder2D(
            sector, 
            self._position, 
            self._view_scale
        )
        vertex, distance = wall_finder.closest_vertex()
        if vertex is not None:
            return highlight_details.HighlightDetails(
                vertex,
                f'{vertex.vertex_part_name}_highlight',
                hit
            ), distance

        wall, distance = wall_finder.closest_wall()
        if wall is not None:
            return highlight_details.HighlightDetails(
                wall,
                wall.default_part,
                hit
            ), distance

        return None, closest_distance
