# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

import yaml

from ... import find_resource
from ..map_objects.sprite.sprite_constants import *
from . import sector_type_descriptor, sprite_type, wall_type_descriptor


def _load_sector_descriptors():
    result: typing.Dict[
        int,
        sector_type_descriptor.SectorTypeDescriptor
    ] = {}

    path = find_resource('sector_types.yaml')
    with open(path, 'r') as file:
        sector_types: dict = yaml.safe_load(file.read())

    for sector_type, descriptor in sector_types.items():
        result[sector_type] = sector_type_descriptor.SectorTypeDescriptor(
            sector_type,
            descriptor
        )

    return result


def _load_wall_descriptors():
    result: typing.Dict[
        int,
        wall_type_descriptor.WallTypeDescriptor
    ] = {}

    path = find_resource('wall_types.yaml')
    with open(path, 'r') as file:
        wall_types: dict = yaml.safe_load(file.read())

    for wall_type, descriptor in wall_types.items():
        result[wall_type] = wall_type_descriptor.WallTypeDescriptor(
            wall_type,
            descriptor
        )

    return result


sector_types = _load_sector_descriptors()
wall_types = _load_wall_descriptors()

reverse_sector_type_lookup = {
    descriptor.name: descriptor.sector_type
    for descriptor in sector_types.values()
}
