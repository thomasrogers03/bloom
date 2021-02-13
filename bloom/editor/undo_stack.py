# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing
from contextlib import contextmanager

from .. import cameras


class UndoableOperation:
    def get_name(self):
        return "Undefined"

    def undo(self):
        raise NotImplementedError()

    def redo(self):
        raise NotImplementedError()


class SimpleUndoableOperation:
    def __init__(self, name: str, undo, redo):
        self._name = name
        self.undo = undo
        self.redo = redo
        self.apply = self.redo

    def get_name(self):
        return self._name


class MapObject:
    def invalidate_geometry(self):
        raise NotImplementedError()


@contextmanager
def _property_change(
    name: str, map_object: MapObject, part: str, property_names: typing.List[str]
):
    old_values: typing.Dict[str, typing.Any] = {}
    new_values: typing.Dict[str, typing.Any] = {}
    stat = map_object.get_stat_for_part(part)

    for property_name in property_names:
        old_values[property_name] = getattr(stat, property_name)

    def _undo():
        map_object.invalidate_geometry()
        for property_name in property_names:
            setattr(stat, property_name, old_values[property_name])

    def _redo():
        map_object.invalidate_geometry()
        for property_name in property_names:
            setattr(stat, property_name, new_values[property_name])

    yield SimpleUndoableOperation(name, _undo, _redo)

    for property_name in property_names:
        new_values[property_name] = getattr(stat, property_name)


class MultiStepUndo(UndoableOperation):
    def __init__(self, name: str):
        self._name = name
        self._operations: typing.List[UndoableOperation] = []

    def add_operation(self, operation: UndoableOperation):
        self._operations.append(operation)

    @property
    def has_operations(self):
        return len(self._operations) > 0

    def get_name(self):
        return self._name

    def undo(self):
        for item in reversed(self._operations):
            item.undo()

    def redo(self):
        for item in self._operations:
            item.redo()


class UndoStack:
    def __init__(self, camera_collection: cameras.Cameras):
        self._camera_collection = camera_collection
        self._undo: typing.List[UndoableOperation] = []
        self._redo: typing.List[UndoableOperation] = []
        self._multi_step_undo: MultiStepUndo = None
        self._enabled = False

    def enable(self):
        self._enabled = True

    def add_operation(self, operation: UndoableOperation):
        if not self._enabled:
            return

        if self._multi_step_undo is None:
            self._redo.clear()
            self._undo.append(operation)
        else:
            self._multi_step_undo.add_operation(operation)

    def undo(self):
        if len(self._undo) < 1:
            self._camera_collection.set_info_text("Nothing to undo...")
            return

        operation = self._undo.pop()
        operation.undo()

        self._camera_collection.set_info_text(f"Undo: {operation.get_name()}")
        self._redo.append(operation)

    def redo(self):
        if len(self._redo) < 1:
            self._camera_collection.set_info_text("Nothing to redo...")
            return

        operation = self._redo.pop()
        operation.redo()

        self._camera_collection.set_info_text(f"Redo: {operation.get_name()}")
        self._undo.append(operation)

    @contextmanager
    def multi_step_undo(self, name: str):
        if self._multi_step_undo is None:
            self.begin_multi_step_undo(name)
            yield
            self.end_multi_step_undo()
        else:
            yield

    def begin_multi_step_undo(self, name: str):
        if self._multi_step_undo is None:
            self._multi_step_undo = MultiStepUndo(name)

    def end_multi_step_undo(self):
        if self._multi_step_undo is not None:
            multi_step_undo = self._multi_step_undo
            self._multi_step_undo = None
            if multi_step_undo.has_operations:
                self.add_operation(multi_step_undo)

    @contextmanager
    def property_change(
        self,
        name: str,
        map_object: MapObject,
        part: str,
        *property_names: typing.List[str],
    ):
        with _property_change(name, map_object, part, property_names) as operation:
            yield
            self.add_operation(operation)
