# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import math
import os.path
import threading
import typing
import uuid
from collections import defaultdict

from direct.showbase import Loader
from direct.task import Task
from panda3d import core

from .. import constants, rff
from . import midi_to_wav, sfx


class SoundAttachment(typing.NamedTuple):
    sound: int
    node_path: core.NodePath
    distance_at_max_volume: float
    distance_to_cut_off: float
    max_volume: float

class Manager:

    def __init__(
        self,
        loader: Loader.Loader,
        task_manager: Task.TaskManager,
        listener: core.NodePath,
        sounds_rff: rff.RFF,
        fluid_synth_path: str,
        sound_font_path: str
    ):
        self._loader = loader
        self._task_manager = task_manager
        self._listener = listener
        self._rff = sounds_rff
        self._fluid_synth_path = fluid_synth_path
        self._sound_font_path = sound_font_path
        self._active_sounds: typing.Dict[int, core.AudioSound] = {}
        self._sound_attachments: typing.List[SoundAttachment] = []
        self._sounds_out_of_range: typing.Dict[int, bool] = defaultdict(lambda: True)

        self._sound_names: typing.Dict[int, str] = {
            index: name
            for name, index in self._rff.find_matching_entries_with_indexes('*.SFX')
        }

        self._task_manager.add(self._update)

    def attach_sound_to_object(
        self,
        attachment: SoundAttachment
    ):
        self._sound_attachments.append(attachment)
        sound_index = attachment.sound
        if sound_index not in self._active_sounds:
            self._active_sounds[sound_index] = self._load_sound(sound_index)

        sound = self._active_sounds[sound_index]
        if sound is not None:
            sound.set_volume(0)

    def load_music(self, song_name: str):
        if not song_name:
            return

        midi_path = f'cache/{song_name}.mid'
        if not os.path.exists(midi_path):
            song_data = self._rff.data_for_entry(f'{song_name}.MID')
            with open(midi_path, 'w+b') as file:
                file.write(song_data)

        converter = midi_to_wav.MidiToWav(midi_path)
        song_path = converter.output_path
        if not os.path.exists(song_path):
            converter.convert(self._fluid_synth_path, self._sound_font_path)

        return self._loader.load_sfx(song_path)

    def _load_sound(self, sound_index: int):
        if sound_index not in self._sound_names:
            return None

        sound = self._get_sfx(sound_index)
        if sound is None:
            return None

        sound_path = f'cache/{sound_index}.wav'
        if not os.path.exists(sound_path):
            if sound is None or not sound.has_data:
                return None
            sound.create_wav(sound_path)

        result = self._loader.load_sfx(sound_path)
        result.set_play_rate(sound.pitch)

        return result

    def _get_sfx(self, sound_index):
        if sound_index not in self._sound_names:
            return None

        sound_name = self._sound_names[sound_index]
        return sfx.Sound.load(self._rff, sound_name)

    def clear(self):
        for sound in self._active_sounds.values():
            sound.stop()
            self._loader.unload_sfx(sound)
        self._active_sounds.clear()

    def _update(self, task):
        remove_indices = []
        volumes = defaultdict(lambda: 0)
        for attachment_index, attachment in enumerate(self._sound_attachments):
            if attachment.node_path.is_empty():
                remove_indices.append(attachment_index)

            distance_squared = attachment.node_path.get_pos(self._listener).length_squared()
            cut_off_squared = attachment.distance_to_cut_off * attachment.distance_to_cut_off
            if distance_squared > cut_off_squared:
                continue

            max_volume_distance_squared = attachment.distance_at_max_volume
            if distance_squared <= max_volume_distance_squared:
                portion = 1
            else:
                portion = 1 - math.sqrt(distance_squared) / attachment.distance_to_cut_off
            volume = portion * attachment.max_volume

            if volume > volumes[attachment.sound]:
                volumes[attachment.sound] = volume

        for sound_index, sound in self._active_sounds.items():
            volume = volumes[sound_index]

            if volume > 0:
                sfx_sound = self._get_sfx(sound_index)
                sound.set_volume(volume * sfx_sound.relative_volume)
                if sound.status() != core.AudioSound.PLAYING:
                    if not self._sounds_out_of_range[sound_index]:
                        sound.set_time(sfx_sound.loop_time)
                    sound.play()
                self._sounds_out_of_range[sound_index] = False
            else:
                sound.stop()
                self._sounds_out_of_range[sound_index] = True

        remove_indices = reversed(sorted(remove_indices))
        for index in remove_indices:
            del self._sound_attachments[index]

        return task.cont

    def play_sound_once(self, sound_index: int) -> typing.Tuple[core.AudioSound, typing.Callable[[], None]]:
        sound = self._load_sound(sound_index)
        if sound is not None:
            sound.set_volume(1)
            sound.play()

            task_id = str(uuid.uuid4())
            stop_event = threading.Event()
            self._task_manager.add(
                self._check_unload_sound,
                name=task_id,
                extraArgs=[sound_index, sound, stop_event],
                appendTask=True
            )

            def _stop_sound():
                stop_event.set()
                sound.stop()

            return sound, _stop_sound

        return None, None

    def _check_unload_sound(
        self,
        sound_index: int,
        sound: core.AudioSound,
        stop_event: threading.Event,
        task
    ):
        if sound.status() != core.AudioSound.PLAYING:
            sfx_sound = self._get_sfx(sound_index)
            if sfx_sound.loop_time >= 0 and not stop_event.is_set():
                sound.set_time(sfx_sound.loop_time)
                sound.play()
                return task.cont

            self._loader.unload_sfx(sound)
            return task.done
        return task.cont
