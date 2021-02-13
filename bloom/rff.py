# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing
from collections import defaultdict
from fnmatch import fnmatch

from . import data_loading


class Header(data_loading.CustomStruct):
    magic: data_loading.Magic
    version: data_loading.UInt32
    directory_offset: data_loading.UInt32
    number_of_entries: data_loading.UInt32
    unknowns: data_loading.SizedType(data_loading.UInt32, 4)


class Entry(data_loading.CustomStruct):
    unknown0: data_loading.SizedType(bytes, 16)
    offset: data_loading.UInt32
    size: data_loading.UInt32
    unknown1: data_loading.UInt32
    time: data_loading.UInt32
    flags: data_loading.UInt8
    name: data_loading.FixedLengthString(11)
    indexer: data_loading.UInt32


class RFF:
    _FLAG_ENCRYPTED = 1 << 4

    def __init__(self, path: str):
        with open(path, 'rb') as file:
            data = file.read()
        self._unpacker = data_loading.Unpacker(data)
        self._header = self._unpacker.read_struct(Header)

        self._unpacker.seek(self._header.directory_offset)
        entry_bytesize = Entry.size() * self._header.number_of_entries
        encrypted_entries = bytearray(self._unpacker.get_bytes(entry_bytesize))

        self._crypto_byte = self._header.directory_offset & 0xFF

        for index in range(0, len(encrypted_entries), 2):
            encrypted_entries[index] ^= self._crypto_byte
            encrypted_entries[index+1] ^= self._crypto_byte
            self._crypto_byte = (self._crypto_byte + 1) & 0xFF

        entries = data_loading.Unpacker(encrypted_entries).read_multiple(Entry, self._header.number_of_entries)
        self._entries: typing.Dict[str, Entry] = {}
        self._indexed_entries: typing.Dict[str, typing.Dict[int, Entry]] = defaultdict(lambda: {})
        for entry in entries:
            file_name = entry.name.rstrip('\x00')
            extension = file_name[0:3]
            file_name = f'{file_name[3:]}.{extension}'
            self._entries[file_name] = entry
            self._indexed_entries[extension][entry.indexer] = entry

    def file_listing(self) -> typing.List[str]:
        return list(self._entries.keys())

    def find_matching_entries(self, fnmatcher: str) -> typing.Iterable[str]:
        for entry_name, _ in self._matching_entries(fnmatcher):
            yield entry_name

    def find_matching_entries_with_indexes(self, fnmatcher: str) -> typing.Iterable[typing.Tuple[str, int]]:
        for entry_name, entry in self._matching_entries(fnmatcher):
            yield entry_name, entry.indexer

    def _matching_entries(self, fnmatcher: str) -> typing.Iterable[Entry]:
        fnmatcher = fnmatcher.upper()
        for entry_name, value in self._entries.items():
            if fnmatch(entry_name, fnmatcher):
                yield entry_name, value

    def data_for_entry(self, file_name: str) -> bytes:
        if file_name not in self._entries:
            return None

        entry = self._entries[file_name]
        return self._decrypted_entry(entry)

    def data_for_entry_by_index(self, extension: str, index: int) -> bytes:
        if index not in self._indexed_entries[extension]:
            return None

        entry = self._indexed_entries[extension][index]
        return self._decrypted_entry(entry)

    def _decrypted_entry(self, entry: Entry):
        self._unpacker.seek(entry.offset)
        data = bytearray(self._unpacker.get_bytes(entry.size))
        if (entry.flags & self._FLAG_ENCRYPTED) != 0:
            for index in range(min(256, entry.size)):
                data[index] ^= (index >> 1)

        return bytes(data)
