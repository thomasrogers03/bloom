# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing


class EditMode:

    def __init__(self):
        self._ticker_indices: typing.Dict[str, int] = {}
        self._ticker_names: typing.Dict[int, str] = {}
        self._tickers: typing.List[typing.List[typing.Callable[[], None]]] = []
        self._always_tickers: typing.List[typing.Callable[[], None]] = []
        self._current_mode_index = 0
        self._mode_stack: typing.List[typing.Tuple[int, typing.Callable[[], None]]] = []

    def toggle_mode(self):
        if len(self._tickers) < 1:
            return

        self._current_mode_index = (self._current_mode_index + 1) % len(self._tickers)

    def set_mode(self, name: str):
        self._current_mode_index = self._ticker_indices[name]

    def push_mode(self, name: str, on_pop: typing.Callable[[], None]):
        self._mode_stack.append((self._current_mode_index, on_pop))
        self.set_mode(name)

    def pop_mode(self):
        mode_index, pop_callback = self._mode_stack.pop()
        self._current_mode_index = mode_index
        pop_callback()

    @property
    def current_mode(self):
        return self._ticker_names[self._current_mode_index]

    def always_run(self, callback: typing.Callable[[], None]):
        self._always_tickers.append(callback)

    def __getitem__(self, name: str):
        if name not in self._ticker_indices:
            index = len(self._tickers)
            self._ticker_indices[name] = index
            self._ticker_names[index] = name
            self._tickers.append([])

        return self._tickers[self._ticker_indices[name]]

    def tick(self):
        for ticker in self._always_tickers:
            ticker()

        if len(self._tickers) < 1:
            return

        tickers = self._tickers[self._current_mode_index]
        for ticker in tickers:
            ticker()
