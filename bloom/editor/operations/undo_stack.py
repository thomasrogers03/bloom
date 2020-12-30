# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

class UndoableOperation:

    def undo(self):
        raise NotImplementedError()

    def redo(self):
        raise NotImplementedError()

class UndoStack:

    def __init__(self):
        self._undo: typing.List[UndoableOperation] = []
        self._redo: typing.List[UndoableOperation] = []

    def add_operation(self, operation: UndoableOperation):
        self._redo.clear()
        self._undo.append(operation)

    def undo(self):
        if len(self._undo) < 1:
            return

        operation = self._undo.pop()
        operation.undo()
        self._redo.append(operation)

    def redo(self):
        if len(self._redo) < 1:
            return

        operation = self._redo.pop()
        operation.redo()
        self._undo.append(operation)
