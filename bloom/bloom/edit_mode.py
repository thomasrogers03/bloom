# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from direct.showbase import DirectObject
from direct.task import Task
from panda3d import core

from . import constants
from .edit_modes import base_edit_mode


class EditMode(DirectObject.DirectObject):

    def __init__(self, mouse_watcher: core.MouseWatcher, task_manager: Task.TaskManager):
        super().__init__()

        self._mouse_watcher = mouse_watcher
        self._task_manager = task_manager

        self._current_edit_mode: base_edit_mode.EditMode = None
        self._always_tickers: typing.List[typing.Callable[[], None]] = []
        self._mode_stack: typing.List[base_edit_mode.EditMode] = []

        self._task_manager.do_method_later(constants.TICK_RATE, self._tick, 'global_ticker')
        self.accept('escape', self.pop_mode)

    @property
    def mouse_watcher(self):
        return self._mouse_watcher

    @property
    def task_manager(self):
        return self._task_manager

    def push_mode(self, mode: base_edit_mode.EditMode):
        if self._current_edit_mode is not None:
            self._mode_stack.append(self._current_edit_mode)
            self._current_edit_mode.exit_mode()
        self._current_edit_mode = mode
        self._current_edit_mode.enter_mode()

    def pop_mode(self):
        if len(self._mode_stack) < 1:
            return

        self._current_edit_mode.exit_mode()
        self._current_edit_mode = self._mode_stack.pop()
        self._current_edit_mode.enter_mode()

    @property
    def current_mode(self):
        return self._current_edit_mode

    def always_run(self, callback: typing.Callable[[], None]):
        self._always_tickers.append(callback)

    def _tick(self, task):
        for ticker in self._always_tickers:
            ticker()

        if self._current_edit_mode is not None:
            self._current_edit_mode.tick()

        return task.again
