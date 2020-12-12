# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.showbase import DirectObject
from panda3d import bullet, core

from .. import (cameras, clicker, clicker_factory, constants, edit_menu,
                edit_mode)
from ..editor import map_editor
from ..menu import Menu


class EditMode(DirectObject.DirectObject):

    def __init__(
        self,
        camera_collection: cameras.Cameras,
        menu: edit_menu.EditMenu,
        edit_mode_selector: edit_mode.EditMode
    ):
        super().__init__()

        self._camera_collection = camera_collection
        self._edit_mode_selector = edit_mode_selector
        self._menu = menu

        self._tickers: typing.List[typing.Callable[[], None]] = []
        self._editor: map_editor.MapEditor = None
        self._clicker_factory = clicker_factory.ClickerFactory(
            self._edit_mode_selector.mouse_watcher,
            self._edit_mode_selector.task_manager
        )
        self._events_enabled = True
        self._old_accept = super().accept

        self._context_menu = Menu(camera_collection.aspect_2d)
        self._make_clicker(
            [core.MouseButton.three()],
            on_click=self._show_context_menu,
        )

        self._make_clicker(
            [core.MouseButton.one()],
            on_click=self._hide_context_menu,
            on_click_move=self._hide_context_menu,
        )
        self._make_clicker(
            [core.MouseButton.three()],
            on_click_move=self._hide_context_menu,
        )
        self._make_clicker(
            [core.MouseButton.one(), core.MouseButton.three()],
            on_click=self._hide_context_menu,
            on_click_move=self._hide_context_menu,
        )

    def accept(self, event, method, extraArgs=[]):
        new_handler = self._event_wrapper(method)
        return super().accept(event, new_handler, extraArgs=extraArgs)

    def disable_events(self):
        self._events_enabled = False

    def enable_events(self):
        self._events_enabled = True

    def set_editor(self, editor: map_editor.MapEditor):
        self._editor = editor

    def enter_mode(self, state: dict):
        self._menu.clear()
        self._menu.add_command(
            label="Exit current mode (esc)",
            command=self._exit_current_mode
        )
        self._menu.add_separator()
        self._context_menu.clear()
        self._old_accept(constants.GUI_HAS_FOCUS, self.disable_events)
        self._old_accept(constants.GUI_LOST_FOCUS, self.enable_events)

    def exit_mode(self):
        self._context_menu.hide()
        self.ignore_all()
        return {}

    def _show_context_menu(self):
        position = self._edit_mode_selector.mouse_watcher.get_mouse()
        self._context_menu.show()
        self._context_menu.set_pos(position.x, 0, position.y)

    def _hide_context_menu(self, *_):
        self._context_menu.hide()

    def _exit_current_mode(self):
        self._edit_mode_selector.pop_mode()

    def _event_wrapper(self, handler):
        def _callback(*args, **kwargs):
            if self._events_enabled:
                return handler(*args, **kwargs)
        return _callback

    def _make_clicker(
        self,
        mouse_buttons: typing.List[core.MouseButton],
        on_mouse_down: typing.Callable[[core.Point2], None] = None,
        on_click: typing.Callable[[], None] = None,
        on_double_click: typing.Callable[[], None] = None,
        on_click_move: typing.Callable[[core.Vec2], None] = None,
        on_click_after_move: typing.Callable[[], None] = None,
    ):
        return self._clicker_factory.make_clicker(
            mouse_buttons,
            on_mouse_down=on_mouse_down,
            on_click=on_click,
            on_double_click=on_double_click,
            on_click_move=on_click_move,
            on_click_after_move=on_click_after_move,
        ).append_tick_to(self._tickers)

    def _extrude_mouse_to_scene_transform(self, check_buttons=False):
        if not self._mouse_watcher.has_mouse():
            return None, None

        if check_buttons and any(self._mouse_watcher.is_button_down(button) for button in clicker.Clicker.ALL_MOUSE_BUTTONS):
            return None, None

        mouse = self._mouse_watcher.get_mouse()
        source = core.Point3()
        target = core.Point3()

        self._camera.lens.extrude(mouse, source, target)

        source = self._camera_collection.scene.get_relative_point(
            self._camera.camera, source)
        target = self._camera_collection.scene.get_relative_point(
            self._camera.camera, target)

        return source, target

    @property
    def _mouse_watcher(self):
        return self._edit_mode_selector.mouse_watcher

    @property
    def _camera(self) -> cameras.Camera:
        raise NotImplementedError()

    def tick(self):
        if not self._events_enabled:
            return

        for ticker in self._tickers:
            ticker()
            if self._edit_mode_selector.tick_cancelled:
                break
