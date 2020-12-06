# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import inspect
import io
import logging
import struct
import typing
from collections.abc import Iterable

import numpy

logger = logging.getLogger(__name__)

T = typing.TypeVar('T')


class SizedType:

    def __init__(self, variable_type: type, count: int):
        self._variable_type = variable_type
        self._count = count

    def format_string(self) -> bytes:
        callback = getattr(self._variable_type, 'format_string', None)
        if callback is not None:
            return f'{self._count}{callback().decode()}'.encode()

        if self._variable_type == bytes:
            return f'{self._count}s'.encode()

        raise ValueError('Unknown type')

    def size(self):
        callback = getattr(self._variable_type, 'size', None)
        if callback is not None:
            return callback() * self._count

        if self._variable_type == bytes:
            return self._count

        raise ValueError('Unknown type')

    def flatten(self, value: typing.Iterable[T]):
        if self._variable_type == bytes:
            return value[0]

        return list(value)

    def unflatten(self, value: typing.Iterable[T]):
        if self._variable_type == bytes:
            return [value]

        return value

    def default(self):
        callback = getattr(self._variable_type, 'default', None)
        if callback is not None:
            return [callback()] * self._count

        if self._variable_type == bytes:
            return b'\0' * self._count

        raise ValueError('Unknown type')


class FixedLengthString:

    def __init__(self, count: int):
        self._count = count

    def format_string(self) -> bytes:
        return f'{self._count}s'.encode()

    def size(self):
        return self._count

    def flatten(self, value: typing.Iterable[T]):
        return value[0].decode()

    def unflatten(self, value: str):
        return [value.encode()]

    def default(self):
        return b'\0' * self._count


class FixedSizeInteger:

    def __init__(self, size: int, signed=True):
        self._size = size
        self._signed = signed

    def format_string(self) -> bytes:
        if self._signed:
            if self._size == 1:
                return b'b'
            if self._size == 2:
                return b'h'
            if self._size == 4:
                return b'i'
        else:
            if self._size == 1:
                return b'B'
            if self._size == 2:
                return b'H'
            if self._size == 4:
                return b'I'

        raise ValueError(f'Invalid integer size {self._size}')

    def size(self):
        return self._size

    def flatten(self, value: typing.Iterable[T]):
        return value[0]

    def unflatten(self, value: T):
        return [value]

    def default(self):
        return 0


Int8 = FixedSizeInteger(1)
Int16 = FixedSizeInteger(2)
Int32 = FixedSizeInteger(4)
UInt8 = FixedSizeInteger(1, signed=False)
UInt16 = FixedSizeInteger(2, signed=False)
UInt32 = FixedSizeInteger(4, signed=False)

Magic = SizedType(bytes, 4)


class PartialInteger:

    def __init__(self, expected_integer_type: FixedSizeInteger, bits: int):
        self._bits = bits
        self._expected_size = expected_integer_type.size() * 8

    def size(self):
        return self._bits / 8.0

    @property
    def bits(self):
        return self._bits

    @staticmethod
    def next_required_for_full_integer(type_hints, index) -> typing.Tuple[int, FixedSizeInteger]:
        if index >= len(type_hints) or not isinstance(type_hints[index], PartialInteger):
            return 0, None

        bits = 0
        count = 0
        expected_size: int = None
        while index < len(type_hints):
            if not isinstance(type_hints[index], PartialInteger):
                raise ValueError('Not enough bits to form a byte')

            if expected_size is None:
                expected_size = type_hints[index]._expected_size

            if expected_size != type_hints[index]._expected_size:
                raise ValueError('Found incomplete partial integer')

            bits += type_hints[index].bits
            count += 1

            if bits > expected_size:
                raise ValueError(
                    f'Impossible to read partial integers -> reached {bits} bits')
            elif bits == expected_size:
                return count, FixedSizeInteger(expected_size / 8, signed=False)

            index += 1

        raise ValueError('Impossible to read partial integers')

    @staticmethod
    def read_values(type_hints: typing.List['PartialInteger'], read_value: int) -> typing.List[int]:
        result = []
        for hint in type_hints:
            value = read_value & ((1 << hint.bits) - 1)
            read_value >>= hint.bits

            result.append(value)
        return result

    @staticmethod
    def write_value(type_hints: typing.List['PartialInteger'], values: typing.List[int]) -> int:
        result = 0
        bits = 0
        for hint, value in zip(type_hints, values):
            # value = read_value & ((1 << hint.bits) - 1)
            value &= ((1 << hint.bits) - 1)
            result |= value << bits
            bits += hint.bits
        return result

    def default(self):
        return 0


class Unpacker:

    def __init__(self, buffer: bytes):
        self._buffer = buffer
        self._offset = 0

    def read_struct(self, struct_type: type, skip_members=0) -> T:
        hints: typing.Dict[str, typing.Any] = struct_type.type_hints()
        result = struct_type()

        index = 0
        hint_member_names = list(hints.keys())
        hint_hint_types = list(hints.values())
        index += skip_members
        while index < len(hint_hint_types):
            index = self._read_bits(
                result,
                struct_type,
                hint_member_names,
                hint_hint_types,
                index
            )
            if index >= len(hint_hint_types):
                break

            member_name = hint_member_names[index]
            hint_type = hint_hint_types[index]

            if inspect.isclass(hint_type) and issubclass(hint_type, CustomStruct):
                member_value = self.read_struct(hint_type)
            else:
                member_value = self.read_member(hint_type)
            setattr(result, member_name, member_value)
            index += 1

        return result

    def read_multiple_members(self, hint_type, count: int) -> typing.List[T]:
        return [self.read_member(hint_type) for _ in range(count)]

    def read_member(self, hint_type) -> T:
        format_string = hint_type.format_string()

        size = struct.calcsize(format_string)
        member_value = struct.unpack_from(
            format_string,
            self._buffer,
            self._offset
        )
        member_value = hint_type.flatten(member_value)
        self._offset += size

        return member_value

    def read_multiple(self, struct_type: type, count: int) -> typing.List[T]:
        return [self.read_struct(struct_type) for _ in range(count)]

    @property
    def offset(self):
        return self._offset

    @property
    def data_left(self):
        return len(self._buffer) - self._offset

    def seek(self, offset: int):
        self._offset = offset

    def seek_incrementally(self, amount: int):
        self._offset += amount

    def get_bytes(self, count: int) -> bytes:
        data = self._buffer[self._offset:self._offset+count]
        self._offset += count

        return data

    def read_remaining(self) -> bytes:
        return self.get_bytes(self.data_left)

    def get_xor_encrypted_bytes(self, count: int, key: int) -> bytes:
        data = bytearray(self.get_bytes(count))
        for index in range(count):
            data[index] ^= (key + index) & 0xFF
        return bytes(data)

    def read_xor_encrypted_member(self, hint_type, key: int) -> T:
        data = self.get_xor_encrypted_bytes(hint_type.size(), key)
        return Unpacker(data).read_member(hint_type)

    def read_multiple_xor_encrypted_members(self, hint_type, count: int, key: int) -> typing.List[T]:
        data = self.get_xor_encrypted_bytes(hint_type.size() * count, key)
        return Unpacker(data).read_multiple_members(hint_type, count)

    def read_xor_encrypted_struct(self, struct_type: type, key: int) -> T:
        data = self.get_xor_encrypted_bytes(struct_type.size(), key)
        return Unpacker(data).read_struct(struct_type)

    def read_xor_encrypted_multiple(self, struct_type: type, count: int, key: int) -> typing.List[T]:
        data = self.get_xor_encrypted_bytes(struct_type.size() * count, key)
        return Unpacker(data).read_multiple(struct_type, count)

    def _read_bits(self, result, struct_type, hint_member_names, hint_hint_types, index):
        while True:
            count, integer_type = struct_type.next_required_for_full_integer(
                index
            )

            if integer_type is None:
                break

            bit_member_values = PartialInteger.read_values(
                hint_hint_types[index:index+count],
                self.read_member(integer_type)
            )
            for bit_type_index in range(count):
                setattr(
                    result,
                    hint_member_names[index + bit_type_index],
                    bit_member_values[bit_type_index]
                )

            index += count

        return index


class Packer:

    def __init__(self):
        self._stream = io.BytesIO()

    def get_bytes(self):
        return bytes(self._stream.getbuffer())

    def seek(self, offset):
        self._stream.seek(offset)

    def seek_incrementally(self, amount: int):
        self.seek(self.offset + amount)

    @property
    def offset(self):
        return self._stream.tell()

    def write_struct(self, structure: T):
        hints: typing.Dict[str, typing.Any] = structure.type_hints()

        index = 0
        hint_member_names = list(hints.keys())
        hint_hint_types = list(hints.values())
        while index < len(hint_hint_types):
            index = self._write_bits(
                structure,
                structure.__class__,
                hint_member_names,
                hint_hint_types,
                index
            )
            if index >= len(hint_hint_types):
                break

            member_name = hint_member_names[index]
            hint_type = hint_hint_types[index]
            member_value = getattr(structure, member_name)

            if inspect.isclass(hint_type) and issubclass(hint_type, CustomStruct):
                self.write_struct(member_value)
            else:
                try:
                    self.write_member(hint_type, member_value)
                except struct.error as error:
                    logger.error(f'Error saving {member_name} value {member_value} as {hint_type}')
                    raise
            index += 1

    def write_multiple_members(self, hint_type, members: typing.List[T]):
        for member in members:
            self.write_member(hint_type, member)

    def write_member(self, hint_type, member_value: T):
        format_string = hint_type.format_string()

        size = struct.calcsize(format_string)
        serialized_struct = struct.pack(
            format_string,
            *hint_type.unflatten(member_value)
        )
        self._stream.write(serialized_struct)

    def write_multiple(self, structures: typing.List[T]):
        for structure in structures:
            self.write_struct(structure)

    def _write_bits(self, structure, struct_type, hint_member_names, hint_hint_types, index):
        while True:
            count, integer_type = struct_type.next_required_for_full_integer(
                index
            )

            if integer_type is None:
                break

            values = []
            for bit_type_index in range(count):
                member_value = getattr(
                    structure, hint_member_names[index + bit_type_index]
                )
                values.append(member_value)

            write_value = PartialInteger.write_value(
                hint_hint_types[index:index+count],
                values
            )
            self.write_member(integer_type, write_value)
            index += count

        return index

    def write_bytes(self, data: bytes):
        self._stream.write(data)

    def write_xor_encrypted_bytes(self, data: bytes, key: int):
        encrypted_data = bytearray(data)
        for index in range(len(encrypted_data)):
            encrypted_data[index] ^= (key + index) & 0xFF
        self._stream.write(encrypted_data)

    def write_xor_encrypted_member(self, hint_type, member_value: T, key: int):
        packer = Packer()
        packer.write_member(hint_type, member_value)
        self.write_xor_encrypted_bytes(packer.get_bytes(), key)

    def write_multiple_xor_encrypted_members(self, hint_type, members: typing.List[T], key: int):
        packer = Packer()
        packer.write_multiple_members(hint_type, members)
        self.write_xor_encrypted_bytes(packer.get_bytes(), key)

    def write_xor_encrypted_struct(self, structure: T, key: int):
        packer = Packer()
        packer.write_struct(structure)
        self.write_xor_encrypted_bytes(packer.get_bytes(), key)

    def write_xor_encrypted_multiple(self, structures: typing.List[T], key: int):
        for structure in structures:
            self.write_xor_encrypted_struct(structure, key)


class CustomStruct:

    def __init__(self, **kwargs):
        hints: typing.Dict[str, typing.Any] = self.type_hints()
        for key, hint_type in hints.items():
            if key not in kwargs:
                default = getattr(hint_type, 'default', None)
                if default is not None:
                    value = default()
                else:
                    value = None
                setattr(self, key, value)

        for key, value in kwargs.items():
            if key not in hints:
                raise ValueError(f'Member {key} not in {self.__class__}')
            setattr(self, key, value)

    @classmethod
    def type_hints(cls) -> dict:
        hints = getattr(cls, '_type_hints', None)
        if hints is None:
            cls._type_hints = typing.get_type_hints(cls)
            return cls._type_hints
        return hints

    @classmethod
    def type_hints_list(cls):
        hints = getattr(cls, '_type_hints_list', None)
        if hints is None:
            cls._type_hints_list = list(cls.type_hints().values())
            cls._type_hints_list_bits_cache = [None] * len(cls._type_hints_list)
            return cls._type_hints_list
        return hints

    @classmethod
    def next_required_for_full_integer(cls, index):
        hints = cls.type_hints_list()
        if index >= len(hints):
            return 0, None

        if cls._type_hints_list_bits_cache[index] is None:
            cls._type_hints_list_bits_cache[index] = PartialInteger.next_required_for_full_integer(
                hints,
                index
            )
        return cls._type_hints_list_bits_cache[index]

    def is_default(self):
        hints: typing.Dict[str, typing.Any] = self.type_hints()
        for key, hint_type in hints.items():
            default = getattr(hint_type, 'default', None)
            if default is None:
                return False

            default_value = default()
            value = getattr(self, key)
            if value != default_value:
                return False

        return True

    def copy(self):
        result = self.__class__()
        hints: typing.Dict[str, typing.Any] = self.type_hints()
        for key in hints.keys():
            value = getattr(self, key)
            copied_value = self._copy_value(value)
            setattr(result, key, copied_value)

        return result

    @staticmethod
    def _copy_value(value):
        if isinstance(value, CustomStruct):
            return value.copy()
        elif isinstance(value, Iterable):
            return [CustomStruct._copy_value(inner) for inner in value]
        else:
            return value

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        hints: typing.Dict[str, typing.Any] = self.type_hints()
        for key in hints.keys():
            value = getattr(self, key)
            other_value = getattr(other, key)
            if value != other_value:
                return False

        return True

    def diff(self, other):
        if not isinstance(other, self.__class__):
            return f'{self.__class__} != {other.__class__}'

        result = ''
        hints: typing.Dict[str, typing.Any] = self.type_hints()
        for key in hints.keys():
            value = getattr(self, key)
            other_value = getattr(other, key)
            if value != other_value:
                result += f'{key} -> {value} != {other_value}\n'

        return result

    def __repr__(self, *args, **kwargs):
        return repr(self.__dict__)

    def __str__(self, *args, **kwargs):
        return str(self.__dict__)

    @classmethod
    def size(cls: type):
        hints: typing.Dict[str, typing.Any] = cls.type_hints()
        size = 0
        for hint_type in hints.values():
            size += hint_type.size()
        return int(size)

    @classmethod
    def default(cls: type):
        return cls()
