# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import os.path

from direct.showbase import Audio3DManager, Loader
from panda3d import core

from .. import rff
from . import midi_to_wav, sfx


class Manager:

    def __init__(
        self,
        loader: Loader.Loader,
        sfx_manager: core.AudioManager,
        camera: core.NodePath,
        sounds_rff: rff.RFF,
        fluid_synth_path: str,
        sound_font_path: str
    ):
        self._loader = loader
        self._sfx_manager = sfx_manager
        self._manager_3d = Audio3DManager.Audio3DManager(self._sfx_manager, camera)
        self._rff = sounds_rff
        self._fluid_synth_path = fluid_synth_path
        self._sound_font_path = sound_font_path

        self._sound_names = list(self._rff.find_matching_entries('*.SFX'))

    @property
    def manager_3d(self):
        return self._manager_3d

    def load_music(self, song_name: str):
        if not song_name:
            return

        midi_path = f'cache/{song_name}.mid'
        if not os.path.exists(midi_path):
            song_data = self._sounds_rff.data_for_entry(f'{song_name}.MID')
            with open(midi_path, 'w+b') as file:
                file.write(song_data)

        converter = midi_to_wav.MidiToWav(midi_path)
        song_path = converter.output_path
        if not os.path.exists(song_path):
            converter.convert(self._fluid_synth_path, self._sound_font_path)

        return self._loader.load_sfx(song_path)

    def load_sound(self, sound_index: int):
        sound_name = self._sound_names[sound_index]
        sound_path = f'cache/{sound_name}.wav'
        if not os.path.exists(sound_path):
            sound = sfx.Sound.load(self._rff, sound_name)
            if sound is None:
                return None
            sound.create_wav(sound_path)

        return self._loader.load_sfx(sound_path)
