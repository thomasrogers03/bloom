# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing
from collections import defaultdict

from .map_objects import empty_object


class EventGrouping:

    def __init__(self):
        self._sources: typing.Set[empty_object.EmptyObject] = set()
        self._targets: typing.Set[empty_object.EmptyObject] = set()

    @property
    def sources(self):
        return self._sources

    @property
    def targets(self):
        return self._targets

    @property
    def special_receiver_id(self):
        return None

    @property
    def special_transmitter_id(self):
        return None

class SpecialGrouping:

    def __init__(self, transmitter_id: int, receiver_id: int):
        self._sources: typing.Set[empty_object.EmptyObject] = set()
        self._targets: typing.Set[empty_object.EmptyObject] = set()
        self._transmitter_id = transmitter_id
        self._receiver_id = receiver_id

    @property
    def sources(self):
        return self._sources

    @property
    def targets(self):
        return self._targets

    @property
    def special_receiver_id(self):
        return self._receiver_id

    @property
    def special_transmitter_id(self):
        return self._transmitter_id


class EventGroupingCollection:
    END_LEVEL_GROUPING = SpecialGrouping(None, 4)
    SECRET_END_LEVEL_GROUPING = SpecialGrouping(None, 5)
    START_LEVEL_GROUPING = SpecialGrouping(7, None)

    def __init__(self):
        self._groupings: typing.List[EventGrouping] = []

    def load(
        self, 
        map_objects: typing.List[empty_object.EmptyObject]
    ):
        groupings: typing.Dict[int, EventGrouping] = defaultdict(lambda: EventGrouping())
        groupings[4] = self.END_LEVEL_GROUPING
        groupings[5] = self.SECRET_END_LEVEL_GROUPING
        groupings[7] = self.START_LEVEL_GROUPING

        for item in map_objects:
            data = item.get_data()
            if data.tx_id > 0:
                grouping = groupings[data.tx_id]
                item.set_target_event_grouping(grouping)
            if data.rx_id > 0:
                grouping = groupings[data.rx_id]
                item.set_source_event_grouping(grouping)

        self._groupings[:] = groupings.values()

    def get_grouping(
        self, 
        transmitter: empty_object.EmptyObject, 
        receivers: typing.List[empty_object.EmptyObject]
    ) -> EventGrouping:
        for receiver in receivers:
            if receiver.source_event_grouping is not None:
                if receiver.source_event_grouping.special_transmitter_id is None:
                    return receiver.source_event_grouping

        if transmitter.target_event_grouping is not None:
            if transmitter.target_event_grouping.special_receiver_id is None:
                return transmitter.target_event_grouping
            else:
                return None

        return self._new_grouping()

    def prepare_to_persist(self):
        base_tx_id = 11
        for grouping_index, grouping in enumerate(self._groupings):
            if grouping.special_receiver_id is not None:
                group_id = grouping.special_receiver_id
            elif grouping.special_transmitter_id is not None:
                group_id = grouping.special_transmitter_id
            else:
                group_id = base_tx_id + grouping_index

            for source in grouping.sources:
                source.get_data().tx_id = group_id
            for target in grouping.targets:
                target.get_data().rx_id = group_id

    def _new_grouping(self):
        grouping = EventGrouping()
        self._groupings.append(grouping)
        return grouping
        