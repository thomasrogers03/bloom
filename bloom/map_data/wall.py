# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from .. import data_loading
from . import headers, sector
from ..native import loader


class Stat(data_loading.CustomStruct):
    blocking: data_loading.PartialInteger(data_loading.UInt16, 1)
    bottom_swap: data_loading.PartialInteger(data_loading.UInt16, 1)
    align: data_loading.PartialInteger(data_loading.UInt16, 1)
    xflip: data_loading.PartialInteger(data_loading.UInt16, 1)
    masking: data_loading.PartialInteger(data_loading.UInt16, 1)
    one_way: data_loading.PartialInteger(data_loading.UInt16, 1)
    blocking2: data_loading.PartialInteger(data_loading.UInt16, 1)
    translucent: data_loading.PartialInteger(data_loading.UInt16, 1)
    yflip: data_loading.PartialInteger(data_loading.UInt16, 1)
    translucent_rev: data_loading.PartialInteger(data_loading.UInt16, 1)
    reserved: data_loading.PartialInteger(data_loading.UInt16, 4)
    poly_blue: data_loading.PartialInteger(data_loading.UInt16, 1)
    poly_green: data_loading.PartialInteger(data_loading.UInt16, 1)


class BuildWall(data_loading.CustomStruct):
    position_x: data_loading.Int32
    position_y: data_loading.Int32
    point2_index: data_loading.Int16
    other_side_wall_index: data_loading.Int16
    other_side_sector_index: data_loading.Int16
    stat: Stat
    picnum: data_loading.Int16
    over_picnum: data_loading.Int16
    shade: data_loading.Int8
    palette: data_loading.UInt8
    repeat_x: data_loading.UInt8
    repeat_y: data_loading.UInt8
    panning_x: data_loading.UInt8
    panning_y: data_loading.UInt8
    tags: data_loading.SizedType(data_loading.Int16, 3)


class BloodWallData(data_loading.CustomStruct):
    data1: data_loading.UInt8

    data2: data_loading.PartialInteger(data_loading.UInt8, 6)
    state: data_loading.PartialInteger(data_loading.UInt8, 1)
    data3: data_loading.PartialInteger(data_loading.UInt8, 1)

    data4: data_loading.SizedType(data_loading.UInt8, 2)
    data: data_loading.Int16

    tx_id: data_loading.PartialInteger(data_loading.UInt16, 10)
    data5: data_loading.PartialInteger(data_loading.UInt16, 6)

    rx_id: data_loading.PartialInteger(data_loading.UInt32, 10)
    cmd: data_loading.PartialInteger(data_loading.UInt32, 8)
    going_on: data_loading.PartialInteger(data_loading.UInt32, 1)
    going_off: data_loading.PartialInteger(data_loading.UInt32, 1)
    busy_time: data_loading.PartialInteger(data_loading.UInt32, 12)

    wait_time: data_loading.PartialInteger(data_loading.UInt32, 12)
    rest_state: data_loading.PartialInteger(data_loading.UInt32, 1)
    interruptable: data_loading.PartialInteger(data_loading.UInt32, 1)
    pan_always: data_loading.PartialInteger(data_loading.UInt32, 1)
    panx: data_loading.PartialInteger(data_loading.UInt32, 7)
    data8: data_loading.PartialInteger(data_loading.UInt32, 1)
    pany: data_loading.PartialInteger(data_loading.UInt32, 7)
    data9: data_loading.PartialInteger(data_loading.UInt32, 1)
    decoupled: data_loading.PartialInteger(data_loading.UInt32, 1)

    one_shot: data_loading.PartialInteger(data_loading.UInt8, 1)
    data10: data_loading.PartialInteger(data_loading.UInt8, 1)
    key: data_loading.PartialInteger(data_loading.UInt8, 3)
    push: data_loading.PartialInteger(data_loading.UInt8, 1)
    vector: data_loading.PartialInteger(data_loading.UInt8, 1)
    reserved: data_loading.PartialInteger(data_loading.UInt8, 1)

    data11: data_loading.SizedType(data_loading.UInt8, 2)

    data12: data_loading.PartialInteger(data_loading.UInt8, 2)
    locked: data_loading.PartialInteger(data_loading.UInt8, 1)
    dude_lockout: data_loading.PartialInteger(data_loading.UInt8, 1)
    data13: data_loading.PartialInteger(data_loading.UInt8, 4)

    data14: data_loading.SizedType(data_loading.UInt8, 4)


class Wall(data_loading.CustomStruct):
    wall: BuildWall
    data: BloodWallData


def load_walls(unpacker: data_loading.Unpacker, encrypted: bool, header_3: headers.MapHeader3):
    key = ((header_3.revisions * sector.BuildSector.size()) | 0x4D) & 0xFF

    data = unpacker.buffer
    offset = unpacker.offset
    result, new_offset = loader.load_walls(Wall, data, offset, header_3.wall_count, key)
    unpacker.seek(new_offset)

    return result


def save_walls(packer: data_loading.Packer, encrypted: bool, header_3: headers.MapHeader3, walls: typing.List[Wall]):
    key = ((header_3.revisions * sector.BuildSector.size()) | 0x4D) & 0xFF

    for wall in walls:
        if encrypted:
            packer.write_xor_encrypted_struct(wall.wall, key)
        else:
            packer.write_struct(wall.wall)

        if wall.wall.tags[2] > 0:
            packer.write_struct(wall.data)
