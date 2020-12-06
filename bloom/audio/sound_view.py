# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import typing
from collections import defaultdict

import yaml
from direct.gui import DirectGui, DirectGuiGlobals
from direct.task import Task
from panda3d import core

from .. import constants, edit_mode, find_resource, rff
from ..utils import gui
from . import manager


class SoundView:
    _CANVAS_WIDTH = 1.5
    _DESCRIPTION_WIDTH = 0.5
    _DESCRIPTION_PADDING = 0.02
    _COLUMN_COUNT = _CANVAS_WIDTH / _DESCRIPTION_WIDTH
    _TEXT_FRAME_HEIGHT = 3
    _TEXT_FRAME_SCALE = _TEXT_FRAME_HEIGHT * constants.TEXT_SIZE

    def __init__(
        self,
        parent: core.NodePath,
        audio_manager: manager.Manager,
        task_manager: Task.TaskManager,
        edit_mode_selector: edit_mode.EditMode
    ):
        path = find_resource('sound_names.yaml')
        with open(path, 'r') as file:
            self._sound_descriptors = yaml.safe_load(file.read())
        self._dialog = DirectGui.DirectFrame(
            parent=parent,
            frameSize=(-1.02, 1.02, -0.95, 0.95),
            frameColor=(0.85, 0.85, 0.85, 1),
            relief=DirectGuiGlobals.RAISED,
            borderWidth=(0.01, 0.01)
        )
        self._dialog.hide()

        self._frame = DirectGui.DirectScrolledFrame(
            parent=self._dialog,
            frameColor=(0.65, 0.65, 0.65, 1),
            frameSize=(-1, 1, -0.8, 0.93),
            canvasSize=(0, self._CANVAS_WIDTH, -1, 0),
            scrollBarWidth=0.04,
            relief=DirectGuiGlobals.SUNKEN
        )
        self._bind_scroll(self._frame)

        self._audio_manager = audio_manager
        self._task_manager = task_manager
        self._edit_mode_selector = edit_mode_selector

        self._preview_sound: core.AudioSound = None
        self._selected_sound_index = -1
        self._stop_sound_callback: typing.Callable[[], None] = None
        self._selected_label: DirectGui.DirectButton = None
        self._clicked_label: DirectGui.DirectButton = None
        self._sound_selected: typing.Callable[[int], None] = None

        self._categorized_sound_names: typing.Dict[str, typing.List[int]] = defaultdict(
            lambda: []
        )
        for index, descriptor in self._sound_descriptors.items():
            sounds = self._categorized_sound_names[descriptor['category']]
            sounds.append(index)

        self._labels: typing.Dict[int, DirectGui.DirectButton] = {}
        half_height = self._TEXT_FRAME_SCALE / (2 * constants.TEXT_SIZE)
        for sound_index, descriptor in self._sound_descriptors.items():
            text = f"{sound_index}. {descriptor['name']}"
            label = DirectGui.DirectButton(
                parent=self._canvas,
                frameSize=(
                    0,
                    self._DESCRIPTION_WIDTH / constants.TEXT_SIZE,
                    -half_height,
                    half_height
                ),
                frameColor=(0, 0, 0, 0),
                scale=constants.TEXT_SIZE,
                text=text,
                text_align=core.TextNode.A_left,
                text_wordwrap=(self._DESCRIPTION_WIDTH) / constants.TEXT_SIZE

            )
            self._bind_scroll(label)

            label['extraArgs'] = [label, sound_index, descriptor]
            label['command'] = self._select_sound
            self._labels[sound_index] = label

        self._show_category('misc')

        items = self._categorized_sound_names.keys()
        items = list(sorted(items))
        DirectGui.DirectOptionMenu(
            parent=self._dialog,
            pos=core.Vec3(-1, -0.9),
            items=items,
            scale=constants.TEXT_SIZE,
            text_align=core.TextNode.A_left,
            command=self._show_category
        )

        DirectGui.DirectButton(
            parent=self._dialog,
            pos=core.Vec3(0.8, -0.9),
            text='Ok',
            scale=constants.TEXT_SIZE,
            command=self._confirm
        )
        DirectGui.DirectButton(
            parent=self._dialog,
            pos=core.Vec3(0.92, -0.9),
            text='Cancel',
            scale=constants.TEXT_SIZE,
            command=self._hide
        )

    def show(self, sound_index: int, sound_selected: typing.Callable[[int], None]):
        self._sound_selected = sound_selected

        descriptor = self._sound_descriptors[sound_index]
        self._show_category(descriptor['category'])
        self._select_sound(
            self._labels[sound_index],
            sound_index,
            descriptor
        )

        self._edit_mode_selector.push_mode(self)

    def enter_mode(self, state: dict):
        self._dialog.show()

    def exit_mode(self):
        self._stop_playing()
        self._dialog.hide()
        self._sound_selected = None
        return {}

    def tick(self):
        pass

    def _stop_playing(self):
        if self._preview_sound is not None:
            self._stop_sound_callback()
            self._preview_sound = None

    def _select_sound(
        self,
        label: DirectGui.DirectButton,
        sound_index: int,
        descriptor: dict
    ):
        self._stop_playing()

        if self._selected_label is not None:
            self._selected_label['frameColor'] = (0, 0, 0, 0)

        self._preview_sound, self._stop_sound_callback = self._audio_manager.play_sound_once(
            sound_index
        )
        
        if label == self._clicked_label:
            self._confirm()
            return

        self._clicked_label = label
        self._task_manager.do_method_later(
            constants.DOUBLE_CLICK_TIMEOUT, 
            self._reset_selected_label,
            'reset_selected_label'
        )

        self._selected_label = label
        self._selected_label['frameColor'] = (0, 0, 1, 1)
        self._selected_sound_index = sound_index

    def _reset_selected_label(self, task):
        self._clicked_label = None
        return task.done

    def _show_category(self, category: str):
        for label in self._labels.values():
            label.hide()

        top = 0
        for label_index, label in enumerate(self._labels_for_category(category)):
            column = label_index % self._COLUMN_COUNT
            row = label_index // self._COLUMN_COUNT

            x = column * (self._DESCRIPTION_WIDTH + self._DESCRIPTION_PADDING)
            top = -(row * self._TEXT_FRAME_SCALE + constants.TEXT_SIZE)

            label.set_pos(x, 0, top)
            label.show()

        canvas_size = list(self._frame['canvasSize'])
        canvas_size[2] = top - self._TEXT_FRAME_SCALE
        self._frame['canvasSize'] = canvas_size

    def _labels_for_category(self, category: str):
        return [
            self._labels[index]
            for index in self._categorized_sound_names[category]
        ]

    def _bind_scroll(self, control):
        gui.bind_scroll(control, self._scroll_up, self._scroll_down)

    def _scroll_up(self, event):
        new_value = self._scroll_bar.getValue() - 0.03
        if new_value < 0:
            new_value = 0
        self._scroll_bar.setValue(new_value)

    def _scroll_down(self, event):
        new_value = self._scroll_bar.getValue() + 0.03
        if new_value > 1:
            new_value = 1
        self._scroll_bar.setValue(new_value)

    def _confirm(self):
        self._sound_selected(self._selected_sound_index)
        self._hide()

    def _hide(self):
        self._edit_mode_selector.pop_mode()

    @property
    def _canvas(self):
        return self._frame.getCanvas()

    @property
    def _scroll_bar(self) -> DirectGui.DirectScrollBar:
        return self._frame.verticalScroll
