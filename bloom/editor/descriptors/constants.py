# Copyright 2020 Thmas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

import yaml

from ... import find_resource
from . import sector_type_descriptor, sprite_type, wall_type_descriptor
from ..map_objects import sprite_type_descriptor


_SPRITE_CATEGORIES_TYPE = typing.Dict[
    str,
    typing.List[sprite_type.SpriteType]
]


def _load_sprite_categories():
    path = find_resource('sprite_categories.yaml')
    with open(path, 'r') as file:
        return yaml.safe_load(file.read())


def _load_sprite_descriptors():
    result: typing.Dict[int, sprite_type_descriptor.Descriptor] = {}

    path = find_resource('sprite_types.yaml')
    with open(path, 'r') as file:
        sprite_types: dict = yaml.safe_load(file.read())

    for sprite_type, descriptor in sprite_types.items():
        result[sprite_type] = sprite_type_descriptor.Descriptor(
            sprite_type,
            descriptor
        )
    return result


def _categorized_sprites(
    category_names: typing.Iterable[str],
    sprite_types: typing.Dict[int, sprite_type_descriptor.Descriptor]
):
    category_names = sorted(category_names)
    category_names = list(category_names)

    result: _SPRITE_CATEGORIES_TYPE = {
        category_name: []
        for category_name in category_names
    }

    for descriptor in sprite_types.values():
        result[descriptor.category].append(descriptor)

    return result


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


sprite_category_descriptors = _load_sprite_categories()
sprite_types = _load_sprite_descriptors()
categorized_sprites = _categorized_sprites(
    sprite_category_descriptors.keys(),
    sprite_types
)
sector_types = _load_sector_descriptors()
wall_types = _load_wall_descriptors()

reverse_sector_type_lookup = {
    descriptor.name: descriptor.sector_type
    for descriptor in sector_types.values()
}
