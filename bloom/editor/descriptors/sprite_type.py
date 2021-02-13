# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from .. import map_objects
from ..map_objects.sprite import type_descriptor
from . import object_property


class SpriteType:
    _DECORATION_CATEGORY = 'decoration'

    def __init__(self, descriptor: type_descriptor.Descriptor):
        self._descriptor = descriptor

    def get_sprite_properties(self, sprite: map_objects.EditorSprite, droppables: typing.Dict[str, int]):
        stat = sprite.sprite.sprite.stat
        data = sprite.sprite.data

        properties: typing.Dict[str, object_property.Property] = {
            'State': object_property.Property.create_enum(data.state, object_property.Property.STATE_ENUM),
            'Command': object_property.Property.create_enum(data.cmd, object_property.Property.COMMAND_ENUM),
            'Going On': object_property.Property.create_boolean(data.going_on),
            'Going Off': object_property.Property.create_boolean(data.going_off),
            'Busy Time': object_property.Property.create_integer(data.busy_time),
            'Wait Time': object_property.Property.create_integer(data.wait_time),
            'Interruptable': object_property.Property.create_boolean(data.interruptable),
            'Drop Item': object_property.Property.create_integer(data.drop_item),
            'Decoupled': object_property.Property.create_boolean(data.decoupled),
            'One Shot': object_property.Property.create_boolean(data.one_shot),
            'Key': object_property.Property.create_enum(data.key, object_property.Property.KEY_ENUM),
            'Push': object_property.Property.create_boolean(data.push),
            'Shoot At It': object_property.Property.create_boolean(data.vector),
            'Impact': object_property.Property.create_boolean(data.impact),
            'Pickup': object_property.Property.create_boolean(data.pickup),
            'Touch': object_property.Property.create_boolean(data.touch),
            'Sight': object_property.Property.create_boolean(data.sight),
            'Proximity': object_property.Property.create_boolean(data.proximity),
            'Monsters Cannot Use': object_property.Property.create_boolean(data.dude_lockout),
            'Skill 1': object_property.Property.create_boolean(data.launch_1, offset=True),
            'Skill 2': object_property.Property.create_boolean(data.launch_2, offset=True),
            'Skill 3': object_property.Property.create_boolean(data.launch_3, offset=True),
            'Skill 4': object_property.Property.create_boolean(data.launch_4, offset=True),
            'Skill 5': object_property.Property.create_boolean(data.launch_5, offset=True),
            'Bloodbath': object_property.Property.create_boolean(data.launch_B, offset=True),
            'Cooperative': object_property.Property.create_boolean(data.launch_C, offset=True),
            'Locked': object_property.Property.create_boolean(data.locked),
            'Locked Message': object_property.Property.create_integer(data.lock_msg),
            'Invisible': object_property.Property.create_boolean(stat.invisible),
            'Drop Item': object_property.Property.create_enum(data.drop_item, droppables),
        }

        for descriptor in self._descriptor.property_descriptors:
            name = descriptor['name']
            property_type = descriptor['type']

            value_from = descriptor['from']
            if value_from == 'data_1':
                value = data.data1
            elif value_from == 'data_2':
                value = data.data2
            elif value_from == 'data_3':
                value = data.data3
            elif value_from == 'data_4':
                value = data.data4
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

    def apply_sprite_properties(
        self,
        sprite: map_objects.EditorSprite,
        values: typing.Dict[str, typing.Union[bool, int]]
    ):
        stat = sprite.sprite.sprite.stat
        data = sprite.sprite.data

        data.state = int(values['State'])
        data.cmd = int(values['Command'])
        data.going_on = int(values['Going On'])
        data.going_off = int(values['Going Off'])
        data.busy_time = int(values['Busy Time'])
        data.wait_time = int(values['Wait Time'])
        data.interruptable = int(values['Interruptable'])
        data.drop_item = int(values['Drop Item'])
        data.decoupled = int(values['Decoupled'])
        data.one_shot = int(values['One Shot'])
        data.key = int(values['Key'])
        data.push = int(values['Push'])
        data.vector = int(values['Shoot At It'])
        data.impact = int(values['Impact'])
        data.pickup = int(values['Pickup'])
        data.touch = int(values['Touch'])
        data.sight = int(values['Sight'])
        data.proximity = int(values['Proximity'])
        data.dude_lockout = int(values['Monsters Cannot Use'])
        data.launch_1 = int(values['Skill 1'])
        data.launch_2 = int(values['Skill 2'])
        data.launch_3 = int(values['Skill 3'])
        data.launch_4 = int(values['Skill 4'])
        data.launch_5 = int(values['Skill 5'])
        data.launch_B = int(values['Bloodbath'])
        data.launch_C = int(values['Cooperative'])
        data.locked = int(values['Locked'])
        data.lock_msg = int(values['Locked Message'])
        stat.invisible = int(values['Invisible'])
        data.drop_item = int(values['Drop Item'])

        for descriptor in self._descriptor.property_descriptors:
            name = descriptor['name']
            value = int(values[name])

            value_from = descriptor['from']
            if value_from == 'data_1':
                data.data1 = value
            elif value_from == 'data_2':
                data.data2 = value
            elif value_from == 'data_3':
                data.data3 = value
            elif value_from == 'data_4':
                data.data4 = value
            else:
                raise ValueError(f'Unsupported property source {value_from}')
