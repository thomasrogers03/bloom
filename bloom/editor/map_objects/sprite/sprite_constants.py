# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

import yaml

from .... import find_resource
from . import type_descriptor

_SPRITE_CATEGORIES_TYPE = typing.Dict[
    str,
    typing.List[type_descriptor.Descriptor]
]


def _load_sprite_categories():
    path = find_resource('sprite_categories.yaml')
    with open(path, 'r') as file:
        return yaml.safe_load(file.read())


def _load_sprite_descriptors():
    result: typing.Dict[int, type_descriptor.Descriptor] = {}

    path = find_resource('sprite_types.yaml')
    with open(path, 'r') as file:
        sprite_types: dict = yaml.safe_load(file.read())

    for sprite_type, descriptor in sprite_types.items():
        result[sprite_type] = type_descriptor.Descriptor(
            sprite_type,
            descriptor
        )
    return result


def _categorized_sprites(
    category_names: typing.Iterable[str],
    sprite_types: typing.Dict[int, type_descriptor.Descriptor]
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



sprite_category_descriptors = _load_sprite_categories()
sprite_types = _load_sprite_descriptors()
categorized_sprites = _categorized_sprites(
    sprite_category_descriptors.keys(),
    sprite_types
)

