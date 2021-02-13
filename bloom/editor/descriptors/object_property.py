# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing


class Property(typing.NamedTuple):
    INTEGER_PROPERTY = "int"
    BOOLEAN_PROPERTY = "bool"
    SOUND_PROPERTY = "sound"
    ENUM_PROPERTY = "enum"

    STATE_ENUM = {
        "Off": 0,
        "On": 1,
    }
    COMMAND_ENUM = {
        "Off": 0,
        "On": 1,
        "State": 2,
        "Toggle": 3,
        "Opposite State": 4,
        "Link": 5,
        "Lock": 6,
        "Unlock": 7,
        "Toggle Lock": 8,
        "Stop Off": 9,
        "Stop On": 10,
        "Stop Next": 11,
    }
    KEY_ENUM = {
        "None": 0,
        "Skull Key": 1,
        "Eye Key": 2,
        "Fire Key": 3,
        "Dagger Key": 4,
        "Spider Key": 5,
        "Moon Key": 6,
        "Key 7": 7,
    }
    WAVE_ENUM = {
        "Sine": 0,
        "Linear": 1,
        "Slow Off": 2,
        "Slow On": 3,
    }

    TILE_LINK_OFFSET = "offset"

    property_type: str
    value: typing.Union[bool, int]
    offset: typing.Union[bool, int]
    tile_link_type: str
    enum_values: typing.Dict[str, int]

    @staticmethod
    def create_integer(value: int):
        return Property(Property.INTEGER_PROPERTY, value, 0, None, None)

    @staticmethod
    def create_boolean(value: int, offset=False):
        return Property(Property.BOOLEAN_PROPERTY, bool(value), offset, None, None)

    @staticmethod
    def create_enum(value: int, enum_values: typing.Dict[str, int]):
        return Property(Property.ENUM_PROPERTY, value, 0, None, enum_values)

    @property
    def reverse_enum_values(self):
        return {value: key for key, value in self.enum_values.items()}
