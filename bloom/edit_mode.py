# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import logging
import typing
from contextlib import contextmanager

from direct.showbase import DirectObject
from direct.task import Task
from panda3d import core

from . import constants
from .edit_modes import empty_edit_mode

logger = logging.getLogger(__name__)


class EditMode(DirectObject.DirectObject):

    def __init__(self, mouse_watcher: core.MouseWatcher, task_manager: Task.TaskManager):
        super().__init__()

        self._mouse_watcher = mouse_watcher
        self._task_manager = task_manager
        self._cancel_tick = False

        self._current_edit_mode: empty_edit_mode.EditMode = None
        self._always_tickers: typing.List[typing.Callable[[], None]] = []
        self._mode_stack: typing.List[typing.Tuple[empty_edit_mode.EditMode, dict]] = []
        self._current_pstats_name = 'App:Show code:global_ticker'

        self._task_manager.do_method_later(
            constants.TICK_RATE, self._tick, 'global_ticker')
        self.accept('escape', self.pop_mode)

    @property
    def mouse_watcher(self):
        return self._mouse_watcher

    @property
    def task_manager(self):
        return self._task_manager

    @contextmanager
    def track_performance_stats(self, name: str):
        logger.debug(f'Start tracking stats for {name}')

        old_name = self._current_pstats_name
        self._current_pstats_name = f'{self._current_pstats_name}:{name}'
        tracker = core.PStatCollector(self._current_pstats_name)
        tracker.start()
        try:
            yield
        finally:
            tracker.stop()
            self._current_pstats_name = old_name

    def push_mode(self, mode: empty_edit_mode.EditMode):
        if self._current_edit_mode is not None:
            last_state = self._current_edit_mode.exit_mode()
            self._mode_stack.append((self._current_edit_mode, last_state))
        self._current_edit_mode = mode
        self._current_edit_mode.enter_mode({})

        self._cancel_tick = False

    def pop_mode(self):
        if len(self._mode_stack) < 1:
            return

        self._current_edit_mode.exit_mode()
        self._current_edit_mode, last_state = self._mode_stack.pop()
        self._current_edit_mode.enter_mode(last_state)

        self._cancel_tick = True

    @property
    def current_mode(self):
        return self._current_edit_mode

    @property
    def tick_cancelled(self):
        return self._cancel_tick

    def always_run(self, callback: typing.Callable[[], None]):
        self._always_tickers.append(callback)

    def _tick(self, task):
        with self.track_performance_stats('always_tick'):
            for ticker in self._always_tickers:
                ticker()

        if self._current_edit_mode is not None:
            with self.track_performance_stats('current_edit_mode'):
                self._current_edit_mode.tick()

        self._cancel_tick = False
        return task.again
