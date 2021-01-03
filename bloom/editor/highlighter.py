# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import typing

from panda3d import core

from . import map_editor
from .highlighting import highlight_details, target_view
from .map_objects import empty_object, sector, sprite, wall
from .operations import change_selection


class Highlighter:
    _HIGHLIGHTED_COLOUR = core.Vec3(0.75, 0.85, 0.0125)
    _SELECTED_COLOUR = core.Vec3(0.125, 0.125, 1)

    def __init__(self, editor: map_editor.MapEditor):
        self._editor = editor
        self._selected_target_view = target_view.TargetView(self._editor.scene)
        self._highlighted: highlight_details.HighlightDetails = None
        self._selected: typing.List[highlight_details.HighlightDetails] = []
        self._filter_callback: typing.Callable[[highlight_details.HighlightDetails], bool] = None
        self._get_selected_colour_callback: typing.Callable[
            [highlight_details.HighlightDetails],
            core.Vec4
        ] = None

    @property
    def selected(self) -> typing.List[highlight_details.HighlightDetails]:
        return self._selected

    @property
    def highlighted(self) -> highlight_details.HighlightDetails:
        return self._highlighted

    def set_highlighted(self, value: highlight_details.HighlightDetails):
        self.update(lambda _: value)

    def set_filter_callback(self, filter_callback: typing.Callable[[highlight_details.HighlightDetails], bool]):
        self._filter_callback = filter_callback

    def set_get_selected_colour_callback(self, get_selected_colour_callback: typing.Callable[[highlight_details.HighlightDetails], core.Vec4]):
        self._get_selected_colour_callback = get_selected_colour_callback

    def select_append(self, no_append_if_not_selected=False, selected_type_or_types=None) -> typing.List[highlight_details.HighlightDetails]:
        with self._editor.undo_stack.multi_step_undo('Select'):
            if not (self._highlight_valid(selected_type_or_types) and self._selected_are_valid(selected_type_or_types)):
                self.deselect_all()
                return []

            swap_index = self._higlight_selected_index_for_select()
            if swap_index is not None:
                self._move_highlight_to_top_selected(swap_index)
                self.update_selected_target_view()
                return self._selected

            if no_append_if_not_selected:
                self.deselect_all()
                self.update_selection([self._highlighted])
                self.update_selected_target_view()
                return self._selected

            self.update_selection(self._selected + [self._highlighted])
            self.update_selected_target_view()
            return self._selected

    def select(self, selected_type_or_types=None) -> highlight_details.HighlightDetails:
        with self._editor.undo_stack.multi_step_undo('Select'):
            self.deselect_all()
            if not self._highlight_valid(selected_type_or_types):
                return None

            self._selected = [self._highlighted]
            self.update_selected_target_view()
            return self._selected[0]

    def set_selected_objects(self, objects_to_select: typing.List[empty_object.EmptyObject]):
        hit_position = core.Point3(0, 0, 0)
        if self._highlighted is not None:
            hit_position = self._highlighted.hit_position

        self._selected = [
            highlight_details.HighlightDetails(
                map_object, 
                part,
                hit_position
            )
            for map_object in objects_to_select
            for part in map_object.get_all_parts()
        ]
        self.update_selected_target_view()

    def set_selected(self, highlight_details: typing.List[highlight_details.HighlightDetails]):
        for selected in self._selected:
            selected.map_object.hide_highlight(selected.part)
        self._selected = highlight_details
        self.update_selected_target_view()

    def update_selected_target_view(self):
        self._selected_target_view.reset()
        for selected in self._selected:
            self._selected_target_view.show_targets(selected.map_object)

    def update_selection(self, new_selection: typing.List[highlight_details.HighlightDetails]):
        operation = change_selection.ChangeSelection(
            self,
            self._selected,
            new_selection
        )
        self._editor.undo_stack.add_operation(operation)
        operation.apply()

    def _higlight_selected_index_for_select(self):
        if len(self._selected) < 1:
            return None

        for selected_index, selected in enumerate(self._selected):
            if self._highlighted == selected:
                return selected_index

        return None

    def _move_highlight_to_top_selected(self, selected_index):
        previous = self._selected[-1]
        self._selected[-1] = self._highlighted
        self._selected[selected_index] = previous

    def _highlight_valid(self, selected_type_or_types):
        if self._highlighted is None:
            return False

        if selected_type_or_types is None:
            return True

        if not isinstance(selected_type_or_types, list):
            selected_type_or_types = [selected_type_or_types]

        return any(
            isinstance(self._highlighted.map_object, selected_type)
            for selected_type in selected_type_or_types
        )

    def _selected_are_valid(self, selected_type_or_types):
        if selected_type_or_types is None:
            return True

        if not isinstance(selected_type_or_types, list):
            selected_type_or_types = [selected_type_or_types]

        return all(
            any(
                isinstance(selected.map_object, selected_type)
                for selected_type in selected_type_or_types
            )
            for selected in self._selected
        )

    def deselect_all(self):
        self.update_selection([])
        self.update_selected_target_view()

    def update(
        self, 
        higlight_finder: typing.Callable[[highlight_details.HighlightDetails], highlight_details.HighlightDetails]
    ):
        new_highlight = higlight_finder(self._highlighted)
        
        if new_highlight != self._highlighted:
            if self._highlighted is not None:
                self._highlighted.map_object.hide_highlight(self._highlighted.part)

            if new_highlight is None:
                self._highlighted = None
            elif self._filter_callback is None or self._filter_callback(new_highlight):
                self._highlighted = new_highlight

    def update_displays(self, ticks: int):
        colour_scale = ((math.sin(ticks / 6.0) + 1) / 8) + 0.75

        if self._highlighted is not None:
            self._highlighted.map_object.show_highlight(
                self._highlighted.part,
                self._HIGHLIGHTED_COLOUR * colour_scale
            )

        for selected in self._selected:
            if self._get_selected_colour_callback is None:
                selected_colour = self._SELECTED_COLOUR
            else:
                selected_colour = self._get_selected_colour_callback(selected)

            selected.map_object.show_highlight(
                selected.part,
                selected_colour * colour_scale
            )

    def clear(self):
        if self._highlighted is not None:
            self._highlighted.map_object.hide_highlight(self._highlighted.part)
            self._highlighted = None
        self.deselect_all()
