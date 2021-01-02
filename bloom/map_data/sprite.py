# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from .. import data_loading
from ..native import loader
from . import headers


class Stat(data_loading.CustomStruct):
    blocking: data_loading.PartialInteger(data_loading.UInt16, 1)
    translucent: data_loading.PartialInteger(data_loading.UInt16, 1)
    xflip: data_loading.PartialInteger(data_loading.UInt16, 1)
    yflip: data_loading.PartialInteger(data_loading.UInt16, 1)
    facing: data_loading.PartialInteger(data_loading.UInt16, 2)
    one_sided: data_loading.PartialInteger(data_loading.UInt16, 1)
    centring: data_loading.PartialInteger(data_loading.UInt16, 1)
    blocking2: data_loading.PartialInteger(data_loading.UInt16, 1)
    translucent_rev: data_loading.PartialInteger(data_loading.UInt16, 1)
    reserved: data_loading.PartialInteger(data_loading.UInt16, 3)
    poly_blue: data_loading.PartialInteger(data_loading.UInt16, 1)
    poly_green: data_loading.PartialInteger(data_loading.UInt16, 1)
    invisible: data_loading.PartialInteger(data_loading.UInt16, 1)


class BuildSprite(data_loading.CustomStruct):
    position_x: data_loading.Int32
    position_y: data_loading.Int32
    position_z: data_loading.Int32
    stat: Stat
    picnum: data_loading.Int16
    shade: data_loading.Int8
    palette: data_loading.UInt8
    clip_distance: data_loading.UInt8
    filler: data_loading.UInt8
    repeat_x: data_loading.UInt8
    repeat_y: data_loading.UInt8
    offset_x: data_loading.Int8
    offset_y: data_loading.Int8
    sector_index: data_loading.Int16
    status_number: data_loading.Int16
    theta: data_loading.Int16
    owner: data_loading.Int16
    velocity_x: data_loading.Int16
    velocity_y: data_loading.Int16
    velocity_z: data_loading.Int16
    tags: data_loading.SizedType(data_loading.Int16, 3)


class BloodSpriteData(data_loading.CustomStruct):
    sprite_actor_index: data_loading.PartialInteger(data_loading.UInt16, 14)
    state: data_loading.PartialInteger(data_loading.UInt16, 1)
    unknown2: data_loading.PartialInteger(data_loading.UInt16, 1)

    unknown3: data_loading.UInt8
    unknown4: data_loading.UInt8

    tx_id: data_loading.PartialInteger(data_loading.UInt32, 10)
    rx_id: data_loading.PartialInteger(data_loading.UInt32, 10)
    cmd: data_loading.PartialInteger(data_loading.UInt32, 8)
    going_on: data_loading.PartialInteger(data_loading.UInt32, 1)
    going_off: data_loading.PartialInteger(data_loading.UInt32, 1)
    wave: data_loading.PartialInteger(data_loading.UInt32, 2)

    busy_time: data_loading.PartialInteger(data_loading.UInt32, 12)
    wait_time: data_loading.PartialInteger(data_loading.UInt32, 12)
    rest_state: data_loading.PartialInteger(data_loading.UInt32, 1)
    interruptable: data_loading.PartialInteger(data_loading.UInt32, 1)
    unknown5: data_loading.PartialInteger(data_loading.UInt32, 5)
    launch_T: data_loading.PartialInteger(data_loading.UInt32, 1)

    drop_item: data_loading.UInt8

    decoupled: data_loading.PartialInteger(data_loading.UInt16, 1)
    one_shot: data_loading.PartialInteger(data_loading.UInt16, 1)
    unknown6: data_loading.PartialInteger(data_loading.UInt16, 1)
    key: data_loading.PartialInteger(data_loading.UInt16, 3)
    push: data_loading.PartialInteger(data_loading.UInt16, 1)
    vector: data_loading.PartialInteger(data_loading.UInt16, 1)
    impact: data_loading.PartialInteger(data_loading.UInt16, 1)
    pickup: data_loading.PartialInteger(data_loading.UInt16, 1)
    touch: data_loading.PartialInteger(data_loading.UInt16, 1)
    sight: data_loading.PartialInteger(data_loading.UInt16, 1)
    proximity: data_loading.PartialInteger(data_loading.UInt16, 1)
    unknown7: data_loading.PartialInteger(data_loading.UInt16, 2)
    launch_1: data_loading.PartialInteger(data_loading.UInt16, 1)

    launch_2: data_loading.PartialInteger(data_loading.UInt8, 1)
    launch_3: data_loading.PartialInteger(data_loading.UInt8, 1)
    launch_4: data_loading.PartialInteger(data_loading.UInt8, 1)
    launch_5: data_loading.PartialInteger(data_loading.UInt8, 1)
    launch_S: data_loading.PartialInteger(data_loading.UInt8, 1)
    launch_B: data_loading.PartialInteger(data_loading.UInt8, 1)
    launch_C: data_loading.PartialInteger(data_loading.UInt8, 1)
    dude_lockout: data_loading.PartialInteger(data_loading.UInt8, 1)

    data1: data_loading.UInt16
    data2: data_loading.UInt16
    data3: data_loading.UInt16
    unknown8: data_loading.UInt8

    unknown9: data_loading.PartialInteger(data_loading.UInt8, 5)
    locked: data_loading.PartialInteger(data_loading.UInt8, 1)
    unknown10: data_loading.PartialInteger(data_loading.UInt8, 2)

    respawn: data_loading.PartialInteger(data_loading.UInt32, 2)
    data4: data_loading.PartialInteger(data_loading.UInt32, 16)
    unknown11: data_loading.PartialInteger(data_loading.UInt32, 6)
    lock_msg: data_loading.PartialInteger(data_loading.UInt32, 8)

    unknown12: data_loading.UInt8

    unknown13: data_loading.PartialInteger(data_loading.UInt8, 4)
    dude_deaf: data_loading.PartialInteger(data_loading.UInt8, 1)
    dude_ambush: data_loading.PartialInteger(data_loading.UInt8, 1)
    dude_guard: data_loading.PartialInteger(data_loading.UInt8, 1)
    reserved: data_loading.PartialInteger(data_loading.UInt8, 1)

    unknown14: data_loading.SizedType(data_loading.UInt8, 26)

class Sprite(data_loading.CustomStruct):
    sprite: BuildSprite
    data: BloodSpriteData

    @staticmethod
    def new():
        new_blood_sprite = Sprite()
        new_blood_sprite.sprite.tags[2] = -1
        new_blood_sprite.sprite.stat.centring = 1
        new_blood_sprite.sprite.clip_distance = 32
        new_blood_sprite.sprite.velocity_x = 1
        new_blood_sprite.sprite.picnum = 0
        new_blood_sprite.sprite.repeat_x = 64
        new_blood_sprite.sprite.repeat_y = 64

        return new_blood_sprite

def _encryption_key(encrypted: bool, header_3: headers.MapHeader3):
    if encrypted:
        return ((header_3.revisions * BuildSprite.size()) | 0x4D) & 0xFF
    return 0

def load_sprites(unpacker: data_loading.Unpacker, encrypted: bool, header_3: headers.MapHeader3):
    key = _encryption_key(encrypted, header_3)

    data = unpacker.buffer
    offset = unpacker.offset
    result, new_offset = loader.sprites.load_sprites(Sprite, data, offset, header_3.sprite_count, key)
    unpacker.seek(new_offset)

    return result

def save_sprites(packer: data_loading.Packer, encrypted: bool, header_3: headers.MapHeader3, sprites: typing.List[Sprite]):
    key = _encryption_key(encrypted, header_3)

    for sprite in sprites:
        if encrypted:
            packer.write_xor_encrypted_struct(sprite.sprite, key)
        else:
            packer.write_struct(sprite.sprite)

        if sprite.sprite.tags[2] > 0:
            packer.write_struct(sprite.data)
