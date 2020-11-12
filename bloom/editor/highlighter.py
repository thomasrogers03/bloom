# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import core

from . import map_editor
from .map_objects import empty_object, sector, sprite, wall


class HighlightDetails(typing.NamedTuple):
    map_object: typing.Union[
        empty_object.EmptyObject,
        wall.EditorWall,
        sector.EditorSector,
        sprite.EditorSprite
    ]
    part: str
    hit_position: core.Vec3

class Highlighter:
    _HIGHLIGHTED_COLOUR = core.Vec3(0.75, 0.85, 0.0125)
    _SELECTED_COLOUR = core.Vec3(0.125, 0.125, 1)

    def __init__(self, editor: map_editor.MapEditor):
        self._editor = editor
        self._highlighted: HighlightDetails = None
        self._selected: typing.List[HighlightDetails] = []

    @property
    def selected(self) -> typing.List[HighlightDetails]:
        return self._selected

    @property
    def highlighted(self) -> HighlightDetails:
        return self._highlighted

    def select_append(self, no_append_if_not_selected=False, selected_type=None) -> typing.List[HighlightDetails]:
        if not self._highlight_valid(selected_type):
            self.deselect_all()
            return []

        if not self._selected_are_valid(selected_type):
            self.deselect_all()
            return []

        swap_index = self._higlight_selected_index_for_select()
        if swap_index is not None:
            self._move_highlight_to_top_selected(swap_index)
            return self._selected

        if no_append_if_not_selected:
            self.deselect_all()
            self._selected = [self._highlighted]
            return self._selected

        self._selected.append(self._highlighted)
        return self._selected
        
    def select(self, selected_type=None) -> HighlightDetails:
        if not self._highlight_valid(selected_type):
            self.deselect_all()
            return None

        self.deselect_all()
        self._selected = [self._highlighted]
        return self._selected[0]

    def _higlight_selected_index_for_select(self):
        if len(self._selected) < 2:
            return None

        for selected_index, selected in enumerate(self._selected):
            if self._highlighted.map_object == selected.map_object:
                return selected_index
        
        return None

    def _move_highlight_to_top_selected(self, selected_index):
        previous = self._selected[-1]
        self._selected[-1] = self._highlighted
        self._selected[selected_index] = previous
        
    def _highlight_valid(self, selected_type):
        if self._highlighted is None:
            return False

        if selected_type is None:
            return True

        return isinstance(self._highlighted.map_object, selected_type) 

    def _selected_are_valid(self, selected_type):
        if selected_type is None:
            return True

        return all(
            isinstance(selected.map_object, selected_type) 
            for selected in self._selected
        ) 

    def deselect_all(self):
        for selected in self._selected:
            selected.map_object.hide_highlight(selected.part)
        self._selected = []

    def update(self, start_position: core.Point3, end_position: core.Point3):
        new_highlight = self._find_highlight(start_position, end_position)
        if new_highlight != self._highlighted:
            if self._highlighted is not None:
                self._highlighted.map_object.hide_highlight(self._highlighted.part)
            self._highlighted = new_highlight

    def _find_highlight(self, start_position: core.Point3, end_position: core.Point3):
        if self._editor.builder_sector is None:
            return

        direction = end_position - start_position
        search_sector = self._editor.builder_sector
        while True:
            intersect_object, part, hit = search_sector.closest_object_intersecting_line(
                start_position, direction
            )
            if intersect_object is None:
                return None

            if isinstance(intersect_object, wall.EditorWall):
                if part is None:
                    search_sector = intersect_object.other_side_sector
                    start_position = hit
                else:
                    return HighlightDetails(intersect_object, part, hit)
            else:
                return HighlightDetails(intersect_object, part, hit)

        return self._highlighted

    def update_displays(self, ticks: int):
        colour_scale = ((math.sin(ticks / 6.0) + 1) / 8) + 0.75

        if self._highlighted is not None:
            self._highlighted.map_object.show_highlight(
                self._highlighted.part,
                self._HIGHLIGHTED_COLOUR * colour_scale
            )

        for selected in self._selected:
            selected.map_object.show_highlight(
                selected.part,
                self._SELECTED_COLOUR * colour_scale
            )

    def clear(self):
        self._highlighted = None
        self.deselect_all()
