# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from .. import data_loading
from ..rff import RFF


class Header(data_loading.CustomStruct):
    magic: data_loading.Magic
    unknown: data_loading.UInt16
    frame_count: data_loading.UInt8
    unknown2: data_loading.UInt8
    ticks_per_frame: data_loading.UInt16
    unknown3: data_loading.UInt16
    flags: data_loading.UInt32


class Stat(data_loading.CustomStruct):
    tile: data_loading.PartialInteger(data_loading.UInt16, 12)
    translucent_rev: data_loading.PartialInteger(data_loading.UInt16, 1)
    translucent: data_loading.PartialInteger(data_loading.UInt16, 1)
    blocking: data_loading.PartialInteger(data_loading.UInt16, 1)
    hitscan: data_loading.PartialInteger(data_loading.UInt16, 1)


class Frame(data_loading.CustomStruct):
    stat: Stat
    repeat_x: data_loading.UInt8
    repeat_y: data_loading.UInt8

    unknown: data_loading.PartialInteger(data_loading.UInt16, 8)
    palette: data_loading.PartialInteger(data_loading.UInt16, 4)
    smoke: data_loading.PartialInteger(data_loading.UInt16, 1)
    fire_trigger: data_loading.PartialInteger(data_loading.UInt16, 1)
    unknown2: data_loading.PartialInteger(data_loading.UInt16, 2)

    unknown3: data_loading.UInt16


class Seq(typing.NamedTuple):
    header: Header
    frames: typing.List[Frame]


class Manager:

    def __init__(self, rff: RFF):
        self._rff = rff
        self._seqs: typing.Dict[int, typing.Optional[Seq]] = {}

    def get_seq(self, index: int):
        if index not in self._seqs:
            data = self._rff.data_for_entry_by_index('SEQ', index)
            if data is None:
                self._seqs[index] = None
            else:
                loader = data_loading.Unpacker(data)
                header = loader.read_struct(Header)
                frames = loader.read_multiple(Frame, header.frame_count)

                self._seqs[index] = Seq(header, frames)

        return self._seqs[index]
