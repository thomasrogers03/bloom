# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from .. import map_objects


class SpriteProperty(typing.NamedTuple):
    property_type: str
    value: typing.Union[bool, int]
    offset: typing.Union[bool, int]
    tile_link_type: str


class SpriteTypeDescriptor:
    INTEGER_PROPERTY = 'int'
    BOOLEAN_PROPERTY = 'bool'

    TILE_LINK_OFFSET = 'offset'

    _DECORATION_CATEGORY = 'decoration'

    def __init__(self, sprite_type: int, descriptor: dict):
        self._sprite_type = sprite_type
        self._descriptor = descriptor

    @property
    def sprite_repeats(self):
        return self._descriptor.get('repeats', None)

    @property
    def sprite_type(self):
        return self._sprite_type

    @property
    def category(self):
        return self._descriptor['category']

    @property
    def name(self):
        return self._descriptor['name']

    @property
    def palette(self) -> int:
        if 'palette' in self._descriptor:
            return self._descriptor['palette']
        
        if self._descriptor['category'] == self._DECORATION_CATEGORY:
            return None

        return 0

    @property
    def default_tile(self) -> int:
        if 'tile_config' in self._descriptor:
            tile_config = self._descriptor['tile_config']
            if 'tile' in tile_config:
                return tile_config['tile']
            elif 'tiles' in tile_config:
                return tile_config['tiles'][0]
            elif 'start_tile' in tile_config:
                return tile_config['start_tile']

        return 0

    @property
    def valid_tiles(self) -> typing.List[int]:
        if 'tile_config' in self._descriptor:
            tile_config = self._descriptor['tile_config']
            if 'tile' in tile_config:
                return [tile_config['tile']]
            elif 'tiles' in tile_config:
                return tile_config['tiles']
            elif 'start_tile' in tile_config:
                return [tile_config['start_tile']]

        return None

    @property
    def property_descriptors(self) -> typing.List[dict]:
        return self._descriptor.get('properties', [])


    def get_status_number(self, category_descriptors: dict):
        return self._descriptor.get(
            'status_number', 
            category_descriptors[self.category]['status_number']
        )

    def get_sprite_properties(self, sprite: map_objects.EditorSprite):
        data = sprite.sprite.data

        properties: typing.Dict[str, SpriteProperty] = {
            'Receive From': SpriteProperty(self.INTEGER_PROPERTY, data.rx_id, 0, None),
            'Transmit To': SpriteProperty(self.INTEGER_PROPERTY, data.tx_id, 0, None),
            'Going On': SpriteProperty(self.BOOLEAN_PROPERTY, data.going_on, 0, None),
            'Going Off': SpriteProperty(self.BOOLEAN_PROPERTY, data.going_off, 0, None),
            'Busy Time': SpriteProperty(self.INTEGER_PROPERTY, data.busy_time, 0, None),
            'Wait Time': SpriteProperty(self.INTEGER_PROPERTY, data.wait_time, 0, None),
            'Interruptable': SpriteProperty(self.BOOLEAN_PROPERTY, data.interruptable, 0, None),
            'Drop Item': SpriteProperty(self.INTEGER_PROPERTY, data.drop_item, 0, None),
            'Decoupled': SpriteProperty(self.INTEGER_PROPERTY, data.decoupled, 0, None),
            'One Shot': SpriteProperty(self.BOOLEAN_PROPERTY, data.one_shot, 0, None),
            'Key': SpriteProperty(self.INTEGER_PROPERTY, data.key, 0, None),
            'Push': SpriteProperty(self.BOOLEAN_PROPERTY, data.push, 0, None),
            'Shoot At It': SpriteProperty(self.BOOLEAN_PROPERTY, data.vector, 0, None),
            'Impact': SpriteProperty(self.BOOLEAN_PROPERTY, data.impact, 0, None),
            'Pickup': SpriteProperty(self.BOOLEAN_PROPERTY, data.pickup, 0, None),
            'Touch': SpriteProperty(self.BOOLEAN_PROPERTY, data.touch, 0, None),
            'Sight': SpriteProperty(self.BOOLEAN_PROPERTY, data.sight, 0, None),
            'Proximity': SpriteProperty(self.BOOLEAN_PROPERTY, data.proximity, 0, None),
            'Monsters Cannot Use': SpriteProperty(self.BOOLEAN_PROPERTY, data.dude_lockout, 0, None),
            'Skill 1': SpriteProperty(self.BOOLEAN_PROPERTY, data.launch_1, True, None),
            'Skill 2': SpriteProperty(self.BOOLEAN_PROPERTY, data.launch_2, True, None),
            'Skill 3': SpriteProperty(self.BOOLEAN_PROPERTY, data.launch_3, True, None),
            'Skill 4': SpriteProperty(self.BOOLEAN_PROPERTY, data.launch_4, True, None),
            'Skill 5': SpriteProperty(self.BOOLEAN_PROPERTY, data.launch_5, True, None),
            'Bloodbath': SpriteProperty(self.BOOLEAN_PROPERTY, data.launch_B, True, None),
            'Cooperative': SpriteProperty(self.BOOLEAN_PROPERTY, data.launch_C, True, None),
            'Locked': SpriteProperty(self.BOOLEAN_PROPERTY, data.locked, 0, None),
        }

        for descriptor in self.property_descriptors:
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

            if property_type == self.INTEGER_PROPERTY:
                default = 0
            elif property_type == self.BOOLEAN_PROPERTY:
                default = False
            else:
                raise ValueError(f'Unsupported property type {property_type}')

            offset = descriptor.get('offset', default)
            tile_link_type = descriptor.get('link_to_tile', None)

            sprite_property = SpriteProperty(property_type, value, offset, tile_link_type)
            properties[name] = sprite_property

        return properties

    def apply_sprite_properties(
        self, 
        sprite: map_objects.EditorSprite, 
        values: typing.Dict[str, typing.Tuple[bool, int]]
    ):
        data = sprite.sprite.data

        data.rx_id = int(values['Receive From'])
        data.tx_id = int(values['Transmit To'])
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

        for descriptor in self.property_descriptors:
            name = descriptor['name']
            value = values[name]

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
