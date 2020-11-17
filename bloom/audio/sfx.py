# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import wave

from .. import data_loading, rff


class SoundDescriptor(data_loading.CustomStruct):
    relative_volume: data_loading.Int32
    pitch: data_loading.Int32
    pitch_range: data_loading.Int32
    sound_format: data_loading.Int32
    loop_start: data_loading.Int32


class Sound:

    def __init__(self, sounds_rff: rff.RFF, sound_descriptor_data: bytes):
        unpacker = data_loading.Unpacker(sound_descriptor_data)
        self._descriptor = unpacker.read_struct(SoundDescriptor)

        if self._descriptor.sound_format == 1:
            self._sample_rate = 11025
        else:
            self._sample_rate = 22050

        raw_name = unpacker.read_remaining().decode().rstrip('\x00').upper()
        self._raw = sounds_rff.data_for_entry(f'{raw_name}.RAW')

    @staticmethod
    def load(sounds_rff: rff.RFF, sound_sfx_name: str):
        descriptor = sounds_rff.data_for_entry(sound_sfx_name)
        if descriptor is None:
            return None

        return Sound(sounds_rff, descriptor)

    @property
    def pitch(self):
        return self._descriptor.pitch / float(1 << 16)

    @property
    def relative_volume(self):
        return self._descriptor.relative_volume / float(1 << 6)

    @property
    def is_looping(self):
        return self._descriptor.loop_start >= 0

    @property
    def sample_count(self):
        return len(self._raw)

    @property
    def has_data(self):
        return self._raw is not None

    def create_wav(self, path: str):
        with wave.open(path, 'wb') as wave_file:
            wave_file.setnchannels(1)
            wave_file.setsampwidth(1)
            wave_file.setframerate(self._sample_rate)
            wave_file.writeframesraw(self._raw)
