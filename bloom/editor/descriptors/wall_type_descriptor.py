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
            'State': object_property.Property.create_enum(data.state, object_property.Property.STATE_ENUM),
            'Command': object_property.Property.create_enum(data.cmd, object_property.Property.COMMAND_ENUM),

            'Going On': object_property.Property.create_boolean(data.going_on),
            'Going Off': object_property.Property.create_boolean(data.going_off),

            'Busy Time': object_property.Property.create_integer(data.busy_time),
            'Wait Time': object_property.Property.create_integer(data.wait_time),

            'Push': object_property.Property.create_boolean(data.push),
            'Shoot At It': object_property.Property.create_boolean(data.vector),
            'Monsters Cannot Use': object_property.Property.create_boolean(data.dude_lockout),

            'Decoupled': object_property.Property.create_boolean(data.decoupled),
            'One Shot': object_property.Property.create_boolean(data.one_shot),
            'Locked': object_property.Property.create_boolean(data.locked),
            'Interruptable': object_property.Property.create_boolean(data.interruptable),

            'Key': object_property.Property.create_enum(data.key, object_property.Property.KEY_ENUM),

            'X Panning': object_property.Property.create_integer(data.panx),
            'Y Panning': object_property.Property.create_integer(data.pany),
            'Pan Always': object_property.Property.create_boolean(data.pan_always),
        }

        for descriptor in self.property_descriptors:
            name = descriptor['name']
            property_type = descriptor['type']

            value_from = descriptor['from']
            if value_from == 'data':
                value = data.data
            else:
                raise ValueError(f'Unsupported property source {value_from}')

            if property_type == object_property.Property.BOOLEAN_PROPERTY:
                default = False
            else:
                default = 0

            offset = descriptor.get('offset', default)
            tile_link_type = descriptor.get('link_to_tile', None)

            sprite_property = object_property.Property(
                property_type, 
                value, 
                offset, 
                tile_link_type,
                None
            )
            properties[name] = sprite_property


        return properties

    def apply_wall_properties(
        self,
        wall: map_objects.EditorWall,
        values: typing.Dict[str, typing.Tuple[bool, int]]
    ):
        data = wall.blood_wall.data

        data.state = int(values['State'])
        data.cmd = int(values['Command'])

        data.going_on = int(values['Going On'])
        data.going_off = int(values['Going Off'])

        data.busy_time = int(values['Busy Time'])
        data.wait_time = int(values['Wait Time'])

        data.push = int(values['Push'])
        data.vector = int(values['Shoot At It'])
        data.dude_lockout = int(values['Monsters Cannot Use'])

        data.decoupled = int(values['Decoupled'])
        data.one_shot = int(values['One Shot'])
        data.locked = int(values['Locked'])
        data.interruptable = int(values['Interruptable'])

        data.key = int(values['Key'])

        data.panx = int(values['X Panning'])
        data.pany = int(values['Y Panning'])
        data.pan_always = int(values['Pan Always'])

        for descriptor in self.property_descriptors:
            name = descriptor['name']
            value = int(values[name])

            value_from = descriptor['from']
            if value_from == 'data':
                data.data = value
            else:
                raise ValueError(f'Unsupported property source {value_from}')
