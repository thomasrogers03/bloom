# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import data_loading


class MapHeader0(data_loading.CustomStruct):
    magic: data_loading.Magic
    minor_version: data_loading.UInt8
    major_version: data_loading.UInt8

    @staticmethod
    def default():
        return MapHeader0(
            magic=b'BLM\x1a',
            minor_version=0, 
            major_version=7
        )

class MapHeader1(data_loading.CustomStruct):
    player_position: data_loading.SizedType(data_loading.Int32, 3)
    player_theta: data_loading.Int16
    player_sector: data_loading.Int16

    @staticmethod
    def default():
        return MapHeader1(player_sector=-1)

class MapHeader2(data_loading.CustomStruct):
    unknown: data_loading.SizedType(bytes, 6)
    matt: data_loading.FixedLengthString(4)
    unknown_2: data_loading.UInt8

    @staticmethod
    def default():
        return MapHeader2(matt='Matt', unknown_2=2)


class MapHeader3(data_loading.CustomStruct):
    revisions: data_loading.Int32
    sector_count: data_loading.Int16
    wall_count: data_loading.Int16
    sprite_count: data_loading.Int16

    @staticmethod
    def default():
        return MapHeader3(revisions=1)

class MapHeader4(data_loading.CustomStruct):
    copyright: data_loading.FixedLengthString(57)
    unknown: data_loading.SizedType(bytes, 7)
    xsprite: data_loading.UInt32
    xwall: data_loading.UInt32
    xsector: data_loading.UInt32
    unknown_2: data_loading.SizedType(bytes, 52)

    @staticmethod
    def default():
        return MapHeader4(
            copyright='Copyright 1997 Monolith Productions.  All Rights Reserved',
            xsprite=56,
            xwall=24,
            xsector=60,
        )

    