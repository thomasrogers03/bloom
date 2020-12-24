# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from .. import map_objects
from . import object_property


class WallTypeDescriptor:
    def __init__(self, wall_type: int, descriptor: dict):
        self._wall_type = wall_type
        self._descriptor = descriptor

    @property
    def wall_type(self):
        return self._wall_type

    @property
    def name(self):
        return self._descriptor['name']

    @property
    def property_descriptors(self) -> typing.List[dict]:
        return self._descriptor.get('properties', [])

    def get_wall_properties(self, wall: map_objects.EditorWall):
        data = wall.blood_wall.data

        properties: typing.Dict[str, object_property.Property] = {
        }

        for descriptor in self.property_descriptors:
            name = descriptor['name']
            property_type = descriptor['type']

            value_from = descriptor['from']
            value = None
            raise ValueError(f'Unsupported property source {value_from}')

            if property_type == object_property.Property.BOOLEAN_PROPERTY:
                default = False
            else:
                default = 0

            offset = descriptor.get('offset', default)
            tile_link_type = descriptor.get('link_to_tile', None)

            wall_property = object_property.Property(
                property_type, 
                value, 
                offset, 
                tile_link_type,
                None
            )
            properties[name] = wall_property

        return properties

    def apply_wall_properties(
        self,
        wall: map_objects.EditorWall,
        values: typing.Dict[str, typing.Tuple[bool, int]]
    ):
        data = wall.blood_wall.data

        for descriptor in self.property_descriptors:
            name = descriptor['name']
            value = values[name]

            value_from = descriptor['from']
            raise ValueError(f'Unsupported property source {value_from}')
