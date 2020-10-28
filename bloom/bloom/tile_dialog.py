import typing

from direct.gui import DirectGui, DirectGuiGlobals
from panda3d import core

from . import edit_mode


class TileDialog:

    def __init__(
        self,
        parent: core.NodePath,
        get_tile_callback: typing.Callable[[int], core.Texture],
        tile_count: int,
        edit_mode: edit_mode.EditMode
    ):
        self._dialog = DirectGui.DirectFrame(
            parent=parent,
            frameSize=(-1.1, 1.1, -0.9, 0.9)
        )
        self._dialog.hide()
        self._frame = DirectGui.DirectScrolledFrame(
            parent=self._dialog,
            canvasSize=(0, 1, -1, 0),
            frameSize=(-1.05, 1.05, -0.8, 0.88),
            frameColor=(0.65, 0.65, 0.65, 1),
            relief=DirectGuiGlobals.SUNKEN,
        )
        self._canvas = self._frame.getCanvas()

        self._get_tile_callback = get_tile_callback
        self._edit_mode = edit_mode

        self._top = 0.2
        for y in range(int(tile_count / 10)):
            self._top -= 0.2
            for x in range(10):
                pos_x = x * 0.2
                texture: core.Texture = self._get_tile_callback(y * 10 + x)

                width = texture.get_x_size()
                height = texture.get_y_size()
                if width < 1 or height < 1:
                    continue

                if width > height:
                    frame_height = (height / width) * 0.2
                    frame_width = 0.2
                else:
                    frame_height = 0.2
                    frame_width = (width / height) * 0.2
                tile_frame = DirectGui.DirectFrame(
                    parent=self._canvas,
                    pos=core.Vec3(x * 0.2, 0, self._top),
                    frameSize=(0, frame_width, 0, -frame_height),
                    frameTexture=self._get_tile_callback(y * 10 + x)
                )
        frame_size = list(self._frame['canvasSize'])
        frame_size[2] = self._top
        self._frame['canvasSize'] = frame_size

        self._edit_mode['tiles'].append(self._tick)

    def show(self):
        self._dialog.show()
        self._edit_mode.push_mode('tiles')

    def hide(self):
        self._dialog.hide()
        self._edit_mode.pop_mode('tiles')

    def _tick(self):
        pass
