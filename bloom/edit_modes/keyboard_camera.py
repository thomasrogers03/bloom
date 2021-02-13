import typing

from panda3d import core

from .. import cameras
from ..editor import map_editor


class KeyboardCamera:
    _MOVE_AMOUNT = 0.1

    def __init__(
        self,
        camera_collection: cameras.Cameras,
        editor: map_editor.MapEditor,
        accept: typing.Callable[[typing.Callable[[], None]], None],
    ):
        self._camera_collection = camera_collection
        self._editor = editor

        accept("arrow_left", self._move_left)
        accept("arrow_left-repeat", self._move_left)

        accept("arrow_right", self._move_right)
        accept("arrow_right-repeat", self._move_right)

        accept("arrow_down", self._move_back)
        accept("arrow_down-repeat", self._move_back)

        accept("arrow_up", self._move_forward)
        accept("arrow_up-repeat", self._move_forward)

    def _move_left(self):
        self._camera_collection.pan_camera(core.Vec2(-self._MOVE_AMOUNT, 0))
        self._update_editor()

    def _move_right(self):
        self._camera_collection.pan_camera(core.Vec2(self._MOVE_AMOUNT, 0))
        self._update_editor()

    def _move_back(self):
        self._camera_collection.pan_camera(core.Vec2(0, -self._MOVE_AMOUNT))
        self._update_editor()

    def _move_forward(self):
        self._camera_collection.pan_camera(core.Vec2(0, self._MOVE_AMOUNT))
        self._update_editor()

    def _update_editor(self):
        self._editor.update_builder_sector(
            self._camera_collection.get_builder_position()
        )
