# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0


from panda3d import core


class EmptyObject:

    def __init__(self):
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
        raise NotImplementedError

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

    def _get_highlighter(self):
        raise NotImplementedError()
