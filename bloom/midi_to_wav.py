# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import pathlib
import subprocess


class MidiToWav:

    def __init__(self, path_to_midi: str):
        path = pathlib.Path(path_to_midi)
        self._path = str(path)

        extension_cut = -len('.MID')
        path = path_to_midi[:extension_cut] + '.WAV'
        path = pathlib.Path(path)
        self._output_path = str(path)

    def convert(self, sound_font_path: str):
        sound_font_path = pathlib.Path(sound_font_path)
        sound_font_path = str(sound_font_path)

        subprocess.call(['fluidsynth', '-q', '-F', self._output_path, sound_font_path, self._path])
        return self._output_path
