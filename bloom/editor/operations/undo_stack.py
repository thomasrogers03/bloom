# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from ... import cameras
from .. import map_objects
from contextlib import contextmanager


class UndoableOperation:

    def get_name(self):
        return 'Undefined'

    def undo(self):
        raise NotImplementedError()

    def redo(self):
        raise NotImplementedError()


class SimpleUndoableOperation:

    def __init__(self, name: str, undo, redo):
        self._name = name
        self.undo = undo
        self.redo = redo

    def get_name(self):
        return self._name


@contextmanager
def _property_change(name: str, map_object: map_objects.EmptyObject, part: str, property_names: typing.List[str]):
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


class UndoStack:

    def __init__(self, camera_collection: cameras.Cameras):
        self._camera_collection = camera_collection
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

        self._camera_collection.set_info_text(f'Undo: {operation.get_name()}')
        self._redo.append(operation)

    def redo(self):
        if len(self._redo) < 1:
            return

        operation = self._redo.pop()
        operation.redo()

        self._camera_collection.set_info_text(f'Redo: {operation.get_name()}')
        self._undo.append(operation)

    @contextmanager
    def property_change(
        self,
        name: str,
        map_object: map_objects.EmptyObject,
        part: str,
        *property_names: typing.List[str]
    ):
        with _property_change(name, map_object, part, property_names) as operation:
            yield
            self.add_operation(operation)
