# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.showbase import DirectObject
from panda3d import core

from .. import cameras, clicker_factory, constants, editor
from ..editor import grid_snapper, highlighter, map_objects, undo_stack
from ..editor.geometry import move
from ..editor.highlighting import highlight_details
from ..utils import shapes
from . import grid_display


class MovingClicker:
    MOVE_SCALE = constants.TICK_SCALE

    def __init__(
        self,
        map_scene: core.NodePath,
        camera_collection: cameras.Cameras,
        transform_to_camera_delta: typing.Callable[[core.Vec2], core.Vec3],
        object_highlighter: highlighter.Highlighter,
        clickers: clicker_factory.ClickerFactory,
        snapper: grid_snapper.GridSnapper,
        all_sectors: map_objects.SectorCollection,
        undos: undo_stack.UndoStack,
        highlighter_filter_types=None,
        move_sprites_on_sectors=True,
    ):
        self._camera_collection = camera_collection
        self._transform_to_camera_delta = transform_to_camera_delta
        self._object_highlighter = object_highlighter
        self._snapper = snapper
        self._all_sectors = all_sectors
        self._highlighter_filter_types = highlighter_filter_types
        self._move_sprites_on_sectors = move_sprites_on_sectors
        self._updated_callback: typing.Callable[[], None] = None
        self._undo_stack = undos

        self._move_clicker = clickers.make_clicker(
            [core.KeyboardButton.control(), core.MouseButton.one()],
            on_click_after_move=self._end_move_selection,
            on_click_move=self._move_selected,
        )
        self._move_clicker_modified = clickers.make_clicker(
            [core.KeyboardButton.shift(), core.MouseButton.one()],
            on_click_after_move=self._end_move_selection,
            on_click_move=self._move_selected_modified,
        )
        self._move_clicker_full_sector = clickers.make_clicker(
            [
                core.KeyboardButton.control(),
                core.KeyboardButton.shift(),
                core.MouseButton.one(),
            ],
            on_click_after_move=self._end_move_selection,
            on_click_move=self._move_entire_sector,
        )

        self._mover: move.Move = None

        self._grid = grid_display.GridDisplay(self._camera_collection, map_scene)
        self._grid.hide()

        self.show_grid = self._grid.show
        self.hide_grid = self._grid.hide

    @property
    def grid_visible(self) -> bool:
        return not self._grid.is_hidden()

    def setup_keyboard(self, acceptor: DirectObject):
        acceptor.accept("g", self._toggle_grid)
        acceptor.accept("[", self._decrease_grid)
        acceptor.accept("]", self._increase_grid)

    def set_updated_callback(self, updated_callback: typing.Callable[[], None]):
        self._updated_callback = updated_callback

    def tick(self):
        self._move_clicker.tick()
        self._move_clicker_modified.tick()
        self._move_clicker_full_sector.tick()
        self._update_grids()

    def _decrease_grid(self):
        self._snapper.decrease_grid()

    def _increase_grid(self):
        self._snapper.increase_grid()

    def _toggle_grid(self):
        if self.grid_visible:
            self._grid.hide()
        else:
            self._grid.show()

    def _end_move_selection(self):
        if self._mover is None:
            return

        self._mover.end_move()
        self._mover = None
        self._hide_grids()

    def _display_move_info(self):
        if len(self._object_highlighter.selected) < 1:
            return

        first_selected = self._object_highlighter.selected[0].map_object
        message = ""
        if isinstance(first_selected, map_objects.EditorSector):
            message = (
                f"Floor: {first_selected.floor_z}, Ceiling: {first_selected.ceiling_z}"
            )
        elif isinstance(first_selected, map_objects.EditorWall):
            point_1 = first_selected.point_1
            point_1_message = f"(x: {point_1.x}, y: {point_1.y})"

            point_2 = first_selected.point_2
            point_2_message = f"(x: {point_2.x}, y: {point_2.y})"

            message = f"Point 1: {point_1_message}, Point 2: {point_2_message}"
        elif isinstance(first_selected, map_objects.EditorSprite):
            point = first_selected.position
            point_message = f"(x: {point.x}, y: {point.y}, z: {point.z})"
            message = f"Position: {point_message}"
        if message:
            self._camera_collection.set_info_text(message)

    def _move_selected(self, total_delta: core.Vec2, delta: core.Vec2):
        if self._setup_mover():
            total_camera_delta = self._transform_to_camera_delta(total_delta)
            self._mover.move(total_camera_delta * self.MOVE_SCALE)
            self._display_move_info()

            if self._updated_callback is not None:
                self._updated_callback()

    def _move_selected_modified(self, total_delta: core.Vec2, delta: core.Vec2):
        if self._setup_mover():
            total_camera_delta = self._transform_to_camera_delta(total_delta)
            self._mover.move_modified(total_camera_delta * self.MOVE_SCALE)
            self._display_move_info()

            if self._updated_callback is not None:
                self._updated_callback()

    def _move_entire_sector(self, total_delta: core.Vec2, delta: core.Vec2):
        if self._setup_sector_wall_mover():
            total_camera_delta = self._transform_to_camera_delta(total_delta)
            self._mover.move_modified(total_camera_delta * self.MOVE_SCALE)
            self._display_move_info()

            if self._updated_callback is not None:
                self._updated_callback()

    def _setup_sector_wall_mover(self):
        if self._mover is None:
            selected = self._object_highlighter.select_append(
                no_append_if_not_selected=True,
                selected_type_or_types=map_objects.EditorSector,
            )
            if len(selected) < 1:
                return False

            self._initialize_mover(selected[-1], True)
        return True

    def _setup_mover(self):
        if self._mover is None:
            selected = self._object_highlighter.select_append(
                no_append_if_not_selected=True,
                selected_type_or_types=self._highlighter_filter_types,
            )
            if len(selected) < 1:
                return False

            self._initialize_mover(selected[-1], False)
        return True

    def _initialize_mover(
        self, highlight: highlight_details.HighlightDetails, move_sector_walls
    ):
        self._mover = move.Move(
            self._object_highlighter.selected,
            highlight,
            self._snapper,
            self._all_sectors,
            self._move_sprites_on_sectors,
            move_sector_walls,
            self._undo_stack,
        )
        self._show_grids()

    def _update_grids(self):
        if len(self._object_highlighter.selected) > 0:
            highlight = self._object_highlighter.selected[-1]
        else:
            highlight = self._object_highlighter.highlighted

        if highlight is None:
            return

        self._grid.update(
            self._snapper, highlight.hit_position, highlight.map_object.get_sector()
        )

    def _show_grids(self):
        self._grid.set_color_scale(1, 1, 1, 1)

    def _hide_grids(self):
        self._grid.set_color_scale(1, 1, 1, 0.35)
