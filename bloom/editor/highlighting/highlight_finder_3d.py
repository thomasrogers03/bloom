# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

from panda3d import core

from .. import map_editor, map_objects
from . import highlight_details, sector_intersect_3d


class HighlightFinder3D:

    def __init__(self, editor: map_editor.MapEditor, start_position: core.Point3, end_position: core.Point3):
        self._editor = editor
        self._start_position = start_position
        self._end_position = end_position

    def find_highlight(self, current_highlight: highlight_details.HighlightDetails):
        if self._editor.builder_sector is None:
            return current_highlight

        start_position = self._start_position
        end_position = self._end_position

        direction = end_position - start_position
        search_sector = self._editor.builder_sector
        while True:
            tester = sector_intersect_3d.SectorIntersect3D(search_sector)
            intersect_object, part, hit = tester.closest_object_intersecting_line(
                start_position, direction
            )
            if intersect_object is None:
                return None

            if isinstance(intersect_object, map_objects.EditorWall):
                if part is None:
                    search_sector = intersect_object.other_side_sector
                    start_position = hit
                else:
                    return self._wall_highlight(intersect_object, part, hit)
            else:
                return highlight_details.HighlightDetails(intersect_object, part, hit)

        return current_highlight

    def _wall_highlight(self, editor_wall: map_objects.EditorWall, part: str, hit: core.Point3):
        tolerance = self._editor.snapper.grid_size
        tolerance_squared = tolerance * tolerance

        snapped_hit = self._editor.snapper.snap_to_grid_2d(hit.xy)
        distance_from_point_1_squared = (
            snapped_hit - editor_wall.point_1
        ).length_squared()

        if distance_from_point_1_squared < tolerance_squared:
            part = f'{editor_wall.vertex_part_name}_highlight'
        else:
            distance_from_point_2_squared = (
                snapped_hit - editor_wall.point_2).length_squared()
            if distance_from_point_2_squared < tolerance_squared:
                editor_wall = editor_wall.wall_point_2
                part = f'{editor_wall.vertex_part_name}_highlight'

        return highlight_details.HighlightDetails(editor_wall, part, hit)
