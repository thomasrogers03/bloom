# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


from contextlib import contextmanager

from panda3d import core

from .. import undo_stack


class EmptyObject:

    def __init__(self, undos: undo_stack.UndoStack):
        self._undo_stack = undos
        self._source_event_grouping = None
        self._target_event_grouping = None

    @property
    def is_marker(self):
        return False

    def get_sector(self):
        raise NotImplementedError()

    def get_geometry_part(self, part: str) -> core.NodePath:
        raise NotImplementedError()

    def get_type(self) -> int:
        raise NotImplementedError()

    def get_shade(self, part: str) -> float:
        raise NotImplementedError()

    def set_shade(self, part: str, value: float):
        raise NotImplementedError()

    def get_picnum(self, part: str) -> int:
        raise NotImplementedError()

    def set_picnum(self, part: str, picnum: int):
        raise NotImplementedError()

    def reset_panning_and_repeats(self, part: str):
        pass

    def get_data(self):
        raise NotImplementedError()

    def get_stat_for_part(self, part: str):
        raise NotImplementedError()

    def show_debug(self):
        pass

    def hide_debug(self):
        pass

    def invalidate_geometry(self):
        raise NotImplementedError()

    def show_highlight(self, part: str, rgb_colour: core.Vec3):
        self._get_highlighter().show_highlight(self.get_geometry_part(part), rgb_colour)

    def hide_highlight(self, part: str):
        self._get_highlighter().hide_highlight(self.get_geometry_part(part))

    @property
    def default_part(self):
        raise NotImplementedError()

    def get_all_parts(self):
        raise NotImplementedError()

    @property
    def source_event_grouping(self):
        return self._source_event_grouping

    @property
    def target_event_grouping(self):
        return self._target_event_grouping

    @property
    def undos(self):
        return self._undo_stack

    def set_source_event_grouping(self, event_grouping):
        if self._source_event_grouping == event_grouping:
            return

        if self._source_event_grouping is not None:
            self._source_event_grouping.targets.remove(self)
        self._source_event_grouping = event_grouping
        if self._source_event_grouping is not None:
            self._source_event_grouping.targets.add(self)

    def set_target_event_grouping(self, event_grouping):
        if self._target_event_grouping == event_grouping:
            return

        if self._target_event_grouping is not None:
            self._target_event_grouping.sources.remove(self)
        self._target_event_grouping = event_grouping
        if self._target_event_grouping is not None:
            self._target_event_grouping.sources.add(self)

    def change_attribute(self, undo, redo):
        operation = ChangeAttribute(self, undo, redo)
        operation.apply()
        self._undo_stack.add_operation(operation)

    @contextmanager
    def change_blood_object(self):
        old_object = self._blood_object.copy()
        yield
        new_object = self._blood_object.copy()

        def _undo():
            self._blood_object = old_object

        def _redo():
            self._blood_object = new_object

        self.change_attribute(_undo, _redo)

    @property
    def _blood_object(self):
        raise NotImplementedError()

    @_blood_object.setter
    def _blood_object(self, value):
        raise NotImplementedError()

    def _get_highlighter(self):
        raise NotImplementedError()


class ChangeAttribute(undo_stack.UndoableOperation):

    def __init__(self, map_object: EmptyObject, undo, redo):
        self._map_object = map_object
        self._undo = undo
        self._redo = redo
        self.apply = self.redo

    def undo(self):
        self._map_object.invalidate_geometry()
        self._undo()

    def redo(self):
        self._map_object.invalidate_geometry()
        self._redo()
