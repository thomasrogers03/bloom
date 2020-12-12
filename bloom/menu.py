# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.gui import DirectGui, DirectGuiGlobals
from direct.task import Task, TaskManagerGlobal
from panda3d import core

from . import constants
from .utils import gui


class Menu:
    _TEXT_SIZE = constants.TEXT_SIZE

    def __init__(self, parent: core.NodePath, parent_menu: 'Menu' = None):
        self._parent = parent
        self._parent_menu = parent_menu
        self._task_manager = TaskManagerGlobal.taskMgr

        self._frame = DirectGui.DirectFrame(
            parent=parent,
            frameSize=(
                -constants.PADDING,
                constants.PADDING,
                0,
                constants.PADDING
            ),
            relief=DirectGuiGlobals.RAISED,
            borderWidth=(0.01, 0.01),
            state=DirectGuiGlobals.NORMAL
        )
        self._frame.hide()
        self._items: typing.List[DirectGui.DirectButton] = []
        self._bottom = 0.0
        self._width = 0.0
        self._sub_menus: typing.List[Menu] = []
        self._mouse_within = False

        self.destroy = self._frame.destroy
        self.set_pos = self._frame.set_pos

        self._frame.bind(DirectGuiGlobals.WITHIN, self._mouse_in)
        self._frame.bind(DirectGuiGlobals.WITHOUT, self._mouse_out)

        self._auto_hide_task: Task.Task = None

    def hide(self, hide_parent=False):
        self._frame.hide()

        if hide_parent:
            if self._parent_menu is not None:
                self._parent_menu.hide(hide_parent=True)
        else:
            self._hide_sub_menus()

        if self._auto_hide_task is not None:
            self._task_manager.remove(self._auto_hide_task)
            self._auto_hide_task = None

    def show(self):
        self._frame.show()
        self._auto_hide_task = self._task_manager.add(self._auto_hide_sub_menus)

    def add_command(self, text: str, command: typing.Callable[[], None]):
        new_button = DirectGui.DirectButton(
            parent=self._frame,
            pos=core.Vec3(0, self._bottom - self._TEXT_SIZE / 2 - constants.PADDING),
            text=text,
            text_align=core.TextNode.A_left,
            scale=self._TEXT_SIZE,
            command=self._wrapped_command(command),
            relief=DirectGuiGlobals.FLAT,
            frameColor=(0, 0, 0, 0)
        )
        self._adjust_frame(new_button)

        return new_button

    def add_sub_menu(self, text: str):
        menu = Menu(self._frame, parent_menu=self)
        menu.set_pos(0, 0, self._bottom)
        self._sub_menus.append(menu)

        frame = self.add_command(text, None)
        frame.bind(DirectGuiGlobals.WITHIN, self._show_sub_menu, extraArgs=[menu])

        return menu

    def clear(self):
        pass

    def _wrapped_command(self, command):
        def _wrapped(*args, **kwargs):
            self.hide(hide_parent=True)
            if command is not None:
                command(*args, **kwargs)

        return _wrapped

    def _auto_hide_sub_menus(self, task: Task.Task):
        if not self._is_mouse_inside():
            for menu in self._sub_menus:
                menu.hide()

        return task.cont

    def _is_mouse_inside(self):
        return self._mouse_within or \
            any(menu._is_mouse_inside() for menu in self._sub_menus)

    def _mouse_in(self, event):
        self._mouse_within = True
        gui.dispatch_has_focus(event)

    def _mouse_out(self, event):
        self._mouse_within = False
        gui.dispatch_lost_focus(event)

    def _show_sub_menu(self, sub_menu: 'Menu', event):
        self._hide_sub_menus()
        sub_menu.show()

    def _hide_sub_menus(self):
        for menu in self._sub_menus:
            menu.hide()

    def _adjust_frame(self, new_button: DirectGui.DirectButton):
        frame_size = new_button.getBounds()
        button_width = (frame_size[1] - frame_size[0]) * self._TEXT_SIZE
        if button_width > self._width:
            self._width = button_width

        for menu in self._sub_menus:
            menu._frame.set_x(self._width + constants.PADDING)

        self._bottom -= self._TEXT_SIZE + 2 * constants.PADDING

        frame_size = list(self._frame['frameSize'])
        frame_size[2] = self._bottom
        frame_size[1] = self._width + constants.PADDING
        self._frame['frameSize'] = frame_size
