# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

import data_loading

from . import headers


class Stat(data_loading.CustomStruct):
    parallax: data_loading.PartialInteger(data_loading.Int16, 1)
    groudraw: data_loading.PartialInteger(data_loading.Int16, 1)
    swapxy: data_loading.PartialInteger(data_loading.Int16, 1)
    expand: data_loading.PartialInteger(data_loading.Int16, 1)
    xflip: data_loading.PartialInteger(data_loading.Int16, 1)
    yflip: data_loading.PartialInteger(data_loading.Int16, 1)
    align: data_loading.PartialInteger(data_loading.Int16, 1)
    masking: data_loading.PartialInteger(data_loading.Int16, 2)
    reserved: data_loading.PartialInteger(data_loading.Int16, 7)


class BuildSector(data_loading.CustomStruct):
    first_wall_index: data_loading.Int16
    wall_count: data_loading.Int16
    ceiling_z: data_loading.Int32
    floor_z: data_loading.Int32
    ceiling_stat: Stat
    floor_stat: Stat

    ceiling_picnum: data_loading.Int16
    ceiling_heinum: data_loading.Int16
    ceiling_shade: data_loading.Int8
    ceiling_palette: data_loading.UInt8
    ceiling_xpanning: data_loading.UInt8
    ceiling_ypanning: data_loading.UInt8
    floor_picnum: data_loading.Int16
    floor_heinum: data_loading.Int16
    floor_shade: data_loading.Int8
    floor_palette: data_loading.UInt8
    floor_xpanning: data_loading.UInt8
    floor_ypanning: data_loading.UInt8
    visibility: data_loading.UInt8
    filler: data_loading.UInt8
    tags: data_loading.SizedType(data_loading.Int16, 3)


class BloodSectorData(data_loading.CustomStruct):
    unknown: data_loading.UInt8
    data2: data_loading.PartialInteger(data_loading.UInt8, 6)
    state: data_loading.PartialInteger(data_loading.UInt8, 1)
    unknown2: data_loading.PartialInteger(data_loading.UInt8, 1)
    unknown3: data_loading.SizedType(data_loading.UInt8, 2)
    data: data_loading.UInt16
    tx_id: data_loading.PartialInteger(data_loading.UInt16, 10)
    on_wave: data_loading.PartialInteger(data_loading.UInt16, 3)
    off_wave: data_loading.PartialInteger(data_loading.UInt16, 3)

    rx_id: data_loading.PartialInteger(data_loading.UInt32, 10)
    cmd: data_loading.PartialInteger(data_loading.UInt32, 8)
    send_at_on: data_loading.PartialInteger(data_loading.UInt32, 1)
    send_at_off: data_loading.PartialInteger(data_loading.UInt32, 1)
    on_busy_time: data_loading.PartialInteger(data_loading.UInt32, 8)
    compressed2: data_loading.PartialInteger(data_loading.UInt32, 4)

    on_wait_time: data_loading.UInt8

    unknown4: data_loading.PartialInteger(data_loading.UInt32, 5)
    interruptable: data_loading.PartialInteger(data_loading.UInt32, 1)
    light_amplitude: data_loading.PartialInteger(data_loading.UInt32, 8)
    light_frequency: data_loading.PartialInteger(data_loading.UInt32, 8)
    on_wait_set: data_loading.PartialInteger(data_loading.UInt32, 1)
    off_wait_set: data_loading.PartialInteger(data_loading.UInt32, 1)
    light_phase: data_loading.PartialInteger(data_loading.UInt32, 8)

    light_wave: data_loading.PartialInteger(data_loading.UInt8, 4)
    shade_always: data_loading.PartialInteger(data_loading.UInt8, 1)
    light_floor: data_loading.PartialInteger(data_loading.UInt8, 1)
    light_ceiling: data_loading.PartialInteger(data_loading.UInt8, 1)
    light_walls: data_loading.PartialInteger(data_loading.UInt8, 1)

    unknown5: data_loading.UInt8

    pan_always: data_loading.PartialInteger(data_loading.UInt8, 1)
    pan_floor: data_loading.PartialInteger(data_loading.UInt8, 1)
    pan_ceiling: data_loading.PartialInteger(data_loading.UInt8, 1)
    drag: data_loading.PartialInteger(data_loading.UInt8, 1)
    underwater: data_loading.PartialInteger(data_loading.UInt8, 1)
    depth: data_loading.PartialInteger(data_loading.UInt8, 3)

    speed: data_loading.PartialInteger(data_loading.UInt32, 8)
    angle: data_loading.PartialInteger(data_loading.UInt32, 11)
    unknown6: data_loading.PartialInteger(data_loading.UInt32, 1)
    decoupled: data_loading.PartialInteger(data_loading.UInt32, 1)
    one_shot: data_loading.PartialInteger(data_loading.UInt32, 1)
    unknown7: data_loading.PartialInteger(data_loading.UInt32, 1)
    key: data_loading.PartialInteger(data_loading.UInt32, 3)
    trigger_push: data_loading.PartialInteger(data_loading.UInt32, 1)
    trigger_vector: data_loading.PartialInteger(data_loading.UInt32, 1)
    reserved: data_loading.PartialInteger(data_loading.UInt32, 1)
    trigger_enter: data_loading.PartialInteger(data_loading.UInt32, 1)
    trigger_exit: data_loading.PartialInteger(data_loading.UInt32, 1)
    trigger_wall_push: data_loading.PartialInteger(data_loading.UInt32, 1)

    colour_lights: data_loading.PartialInteger(data_loading.UInt32, 1)
    unknown8: data_loading.PartialInteger(data_loading.UInt32, 1)
    off_busy_time: data_loading.PartialInteger(data_loading.UInt32, 8)
    unknown9: data_loading.PartialInteger(data_loading.UInt32, 4)
    off_wait_time: data_loading.PartialInteger(data_loading.UInt32, 8)
    unknown10: data_loading.PartialInteger(data_loading.UInt32, 2)
    unknown11: data_loading.PartialInteger(data_loading.UInt32, 4)
    ceiling_palette2: data_loading.PartialInteger(data_loading.UInt32, 4)

    ceiling_zmotion: data_loading.SizedType(data_loading.Int32, 2)
    floor_zmotion: data_loading.SizedType(data_loading.Int32, 2)
    markers: data_loading.SizedType(data_loading.UInt16, 2)

    crush: data_loading.PartialInteger(data_loading.UInt8, 1)
    unknown12: data_loading.PartialInteger(data_loading.UInt8, 7)

    unknown13: data_loading.SizedType(data_loading.UInt8, 2)

    unknown14: data_loading.PartialInteger(data_loading.UInt8, 1)
    damage_type: data_loading.PartialInteger(data_loading.UInt8, 3)
    flooring_palette2: data_loading.PartialInteger(data_loading.UInt8, 4)

    unknown15: data_loading.PartialInteger(data_loading.UInt32, 8)
    locked: data_loading.PartialInteger(data_loading.UInt32, 1)
    wind_vel: data_loading.PartialInteger(data_loading.UInt32, 10)
    wind_ang: data_loading.PartialInteger(data_loading.UInt32, 11)
    wind_always: data_loading.PartialInteger(data_loading.UInt32, 1)
    dude_lockout: data_loading.PartialInteger(data_loading.UInt32, 1)

    theta: data_loading.PartialInteger(data_loading.UInt32, 11)
    z_range: data_loading.PartialInteger(data_loading.UInt32, 5)
    speed2: data_loading.PartialInteger(data_loading.UInt32, 11)
    unknown16: data_loading.PartialInteger(data_loading.UInt32, 1)
    move_always: data_loading.PartialInteger(data_loading.UInt32, 1)
    bob_floor: data_loading.PartialInteger(data_loading.UInt32, 1)
    bob_ceiling: data_loading.PartialInteger(data_loading.UInt32, 1)
    rotate: data_loading.PartialInteger(data_loading.UInt32, 1)


class Sector(data_loading.CustomStruct):
    sector: BuildSector
    data: BloodSectorData


def load_sectors(unpacker: data_loading.Unpacker, encrypted: bool, header_3: headers.MapHeader3):
    key = (header_3.revisions * BuildSector.size()) & 0xFF

    result: typing.List[Sector] = []
    for _ in range(header_3.sector_count):
        if encrypted:
            build_sector = unpacker.read_xor_encrypted_struct(BuildSector, key)
        else:
            build_sector = unpacker.read_struct(BuildSector)

        sector = Sector(sector=build_sector)

        if sector.sector.tags[2] > 0:
            sector.data = unpacker.read_struct(BloodSectorData)
        elif sector.sector.tags[2] == 0 or sector.sector.tags[2] == -1:
            sector.data = BloodSectorData()
        else:
            raise ValueError('Unable to parse sector data')

        result.append(sector)

    return result


def save_sectors(
    packer: data_loading.Packer,
    encrypted: bool,
    header_3: headers.MapHeader3,
    sectors: typing.List[Sector]
):
    key = (header_3.revisions * BuildSector.size()) & 0xFF

    for sector in sectors:
        if encrypted:
            packer.write_xor_encrypted_struct(sector.sector, key)
        else:
            packer.write_struct(sector.sector)

        if sector.sector.tags[2] > 0:
            packer.write_struct(sector.data)
