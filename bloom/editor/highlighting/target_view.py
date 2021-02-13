# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from panda3d import core

from .. import map_objects


class TargetView:
    def __init__(self, map_scene: core.NodePath):
        self._map_scene = map_scene
        self._display_node: core.GeomNode = None
        self._display: core.NodePath = None
        self._seen: typing.Set[map_objects.empty_object.EmptyObject] = set()

    def reset(self):
        if self._display is not None:
            self._display_node = None

            self._display.remove_node()
            self._display = None

            self._seen.clear()

        if not self._map_scene.is_empty():
            self._display_node = core.GeomNode("target_debug")
            self._display = self._map_scene.attach_new_node(self._display_node)
            self._display.set_transparency(True)

    def show_targets(self, source: map_objects.empty_object.EmptyObject):
        self._show_sources(source)
        self._show_targets(source, core.Vec4(1, 0.25, 0.15, 0.8))

    def _show_sources(self, target: map_objects.empty_object.EmptyObject):
        colour = core.Vec4(1, 1, 0, 0.85)

        if target.source_event_grouping is None:
            return

        for source_index, source in enumerate(target.source_event_grouping.sources):
            self._draw_line(source_index, colour, colour, source.origin, target.origin)

    def _show_targets(
        self, source: map_objects.empty_object.EmptyObject, colour: core.Vec4
    ):
        if source in self._seen:
            return
        self._seen.add(source)

        next_colour = core.Vec4(0, 0.5, 1, colour.w / 2)

        if source.target_event_grouping is None:
            return

        for target_index, target in enumerate(source.target_event_grouping.targets):
            self._draw_line(
                target_index, colour, next_colour, source.origin, target.origin
            )
            self._show_targets(target, next_colour)

    def _draw_line(
        self,
        index: int,
        colour: core.Vec4,
        next_colour: core.Vec4,
        point_1: core.Vec3,
        point_2: core.Vec3,
    ):
        segments = core.LineSegs(str(index))
        segments.set_thickness(8)

        segments.set_color(colour)
        segments.draw_to(point_1)
        segments.set_color(next_colour)
        segments.draw_to(point_2)

        segments.create(self._display_node)
