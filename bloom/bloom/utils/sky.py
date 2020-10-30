import typing

from panda3d import core


class Sky:

    def __init__(
        self,
        render_2d: core.NodePath,
        get_tile: typing.Callable[[int], core.Texture],
        start_tile: int,
        sky_offsets: typing.List[int]
    ):
        self._display: core.NodePath = render_2d.attach_new_node('sky')
        textures = [get_tile(start_tile + offset) for offset in sky_offsets]

        width = 2 / len(textures)
        card_maker = core.CardMaker('sky_part')
        card_maker.set_frame(-1, -1 + width, -1, 1)
        card_node = card_maker.generate()
        
        card: core.NodePath = self._display.attach_new_node(card_node)
        card.set_bin('fixed', -1000)
        card.set_depth_write(False)

        left = 0
        for texture_index, texture in enumerate(textures):
            sky_part = self._display.attach_new_node(f'sky_{texture_index}')
            card.copy_to(sky_part)
            card.set_texture(texture, 1)
            sky_part.set_x(left)
            left += width

        card.remove_node()
