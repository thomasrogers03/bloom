import typing

from panda3d import core

from .. import cameras, constants
from ..tiles import manager


class Sky:

    def __init__(
        self,
        camera_collection: cameras.Cameras,
        tile_manager: manager.Manager,
        start_tile: int,
        sky_offsets: typing.List[int]
    ):
        camera = camera_collection.make_gui_camera('sky')
        camera.display_region.set_sort(constants.BACK_MOST)
        camera.display_region.set_active(True)

        display_node = core.PandaNode('sky')
        self._display: core.NodePath = core.NodePath(display_node)
        camera.camera_node.set_scene(self._display)

        textures = [tile_manager.get_tile(start_tile + offset, 0) for offset in sky_offsets]

        width = 2 / len(textures)
        card_maker = core.CardMaker('sky_part')
        card_maker.set_frame(-1, -1 + width, 1, -1)
        card_node = card_maker.generate()

        card: core.NodePath = self._display.attach_new_node(card_node)
        card.set_bin('fixed', constants.BACK_MOST)
        card.set_depth_write(False)
        card.set_two_sided(True)

        left = 0
        for texture_index, texture in enumerate(textures):
            sky_part = self._display.attach_new_node(f'sky_{texture_index}')
            card.copy_to(sky_part)
            card.set_texture(texture, 1)
            sky_part.set_x(left)
            left += width

        card.remove_node()
