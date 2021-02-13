# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing

from .. import map_objects
from . import object_property


class SectorTypeDescriptor:
    def __init__(self, sector_type: int, descriptor: dict):
        self._sector_type = sector_type
        self._descriptor = descriptor

    @property
    def sector_type(self):
        return self._sector_type

    @property
    def name(self):
        return self._descriptor["name"]

    @property
    def property_descriptors(self) -> typing.List[dict]:
        return self._descriptor.get("properties", [])

    @property
    def marker_types(self) -> typing.List[int]:
        markers = self._descriptor.get("markers", [])
        return [marker["type"] for marker in markers]

    def get_sector_type_properties(self, sector: map_objects.EditorSector):
        data = sector.sector.data

        properties: typing.Dict[str, object_property.Property] = {
            "State": object_property.Property.create_enum(
                data.state, object_property.Property.STATE_ENUM
            ),
            "Command": object_property.Property.create_enum(
                data.cmd, object_property.Property.COMMAND_ENUM
            ),
            "Send At On": object_property.Property.create_boolean(data.send_at_on),
            "Busy Time On": object_property.Property.create_integer(data.on_busy_time),
            "Motion Wave At On": object_property.Property.create_enum(
                data.on_wave, object_property.Property.WAVE_ENUM
            ),
            "Wait At On": object_property.Property.create_boolean(data.on_wait_set),
            "Wait Time At On": object_property.Property.create_integer(
                data.on_wait_time
            ),
            "Send At Off": object_property.Property.create_boolean(data.send_at_off),
            "Busy Time Off": object_property.Property.create_integer(
                data.off_busy_time
            ),
            "Motion Wave At Off": object_property.Property.create_enum(
                data.off_wave, object_property.Property.WAVE_ENUM
            ),
            "Wait At Off": object_property.Property.create_boolean(data.off_wait_set),
            "Wait Time At Off": object_property.Property.create_integer(
                data.off_wait_time
            ),
            "Decoupled": object_property.Property.create_boolean(data.decoupled),
            "One Shot": object_property.Property.create_boolean(data.one_shot),
            "Locked": object_property.Property.create_boolean(data.locked),
            "Interruptable": object_property.Property.create_boolean(
                data.interruptable
            ),
            "Monsters Cannot Use": object_property.Property.create_boolean(
                data.dude_lockout
            ),
            "Push": object_property.Property.create_boolean(data.trigger_push),
            "Shoot At It": object_property.Property.create_boolean(data.trigger_vector),
            "Enter": object_property.Property.create_boolean(data.trigger_enter),
            "Exit": object_property.Property.create_boolean(data.trigger_exit),
            "Wall Push": object_property.Property.create_boolean(
                data.trigger_wall_push
            ),
            "Key": object_property.Property.create_enum(
                data.key, object_property.Property.KEY_ENUM
            ),
            "Under Water": object_property.Property.create_boolean(data.underwater),
            "Pan Always": object_property.Property.create_boolean(data.pan_always),
            "Pan Floor": object_property.Property.create_boolean(data.pan_floor),
            "Pan Ceiling": object_property.Property.create_boolean(data.pan_ceiling),
            "Panning Speed": object_property.Property.create_integer(data.speed),
            "Panning Angle": object_property.Property.create_integer(data.angle),
        }

        for descriptor in self.property_descriptors:
            name = descriptor["name"]
            property_type = descriptor["type"]

            value_from = descriptor["from"]
            if value_from == "data_1":
                value = data.data
            elif value_from == "data_2":
                value = data.data2
            else:
                raise ValueError(f"Unsupported property source {value_from}")

            if property_type == object_property.Property.BOOLEAN_PROPERTY:
                default = False
            else:
                default = 0

            offset = descriptor.get("offset", default)
            tile_link_type = descriptor.get("link_to_tile", None)

            sprite_property = object_property.Property(
                property_type, value, offset, tile_link_type, None
            )
            properties[name] = sprite_property

        return properties

    def apply_sector_type_properties(
        self,
        sector: map_objects.EditorSector,
        values: typing.Dict[str, typing.Union[bool, int]],
    ):
        data = sector.sector.data

        data.state = int(values["State"])
        data.cmd = int(values["Command"])

        data.send_at_on = int(values["Send At On"])
        data.on_busy_time = int(values["Busy Time On"])
        data.on_wave = int(values["Motion Wave At On"])
        data.on_wait_set = int(values["Wait At On"])
        data.on_wait_time = int(values["Wait Time At On"])

        data.send_at_off = int(values["Send At Off"])
        data.off_busy_time = int(values["Busy Time Off"])
        data.off_wave = int(values["Motion Wave At Off"])
        data.off_wait_set = int(values["Wait At Off"])
        data.off_wait_time = int(values["Wait Time At Off"])

        data.decoupled = int(values["Decoupled"])
        data.one_shot = int(values["One Shot"])
        data.locked = int(values["Locked"])
        data.interruptable = int(values["Interruptable"])
        data.dude_lockout = int(values["Monsters Cannot Use"])
        data.trigger_push = int(values["Push"])
        data.trigger_vector = int(values["Shoot At It"])
        data.trigger_enter = int(values["Enter"])
        data.trigger_exit = int(values["Exit"])
        data.trigger_wall_push = int(values["Wall Push"])
        data.key = int(values["Key"])
        data.underwater = int(values["Under Water"])

        data.pan_always = int(values["Pan Always"])
        data.pan_floor = int(values["Pan Floor"])
        data.pan_ceiling = int(values["Pan Ceiling"])
        data.speed = int(values["Panning Speed"])
        data.angle = int(values["Panning Angle"])

        for descriptor in self.property_descriptors:
            name = descriptor["name"]
            value = int(values[name])

            value_from = descriptor["from"]
            if value_from == "data_1":
                data.data = value
            elif value_from == "data_2":
                data.data2 = value
            else:
                raise ValueError(f"Unsupported property source {value_from}")
