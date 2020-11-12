import logging
import typing
import uuid

import numpy
from panda3d import core

from .. import cameras, constants
from .map_objects.sector import EditorSector
from .map_objects.wall import EditorWall
from .wall_bunch import ProjectedWall, WallBunch


class ViewClipping:
    _MAX_DEPTH = 1000
    _CLIP_WIDTH = 2048
    _BUNCH_COLOURS = [
        core.Vec4(1, 0, 0, 1),
        core.Vec4(0, 1, 1, 1),
        core.Vec4(0, 0, 1, 1),
        core.Vec4(1, 0, 1, 1),
        core.Vec4(0.5, 1, 0.5, 1),
        core.Vec4(1, 0.5, 1, 1),
        core.Vec4(1, 0.5, 0.5, 1),
        core.Vec4(0.25, 0.25, 0.25, 1),
    ]

    def __init__(
        self,
        start_sector: EditorSector,
        camera_collection: cameras.Cameras,
        clipping_debug: core.NodePath,
        sector_offset=core.Point3(0, 0, 0)
    ):
        self._start_sector = start_sector
        self._clip_buffer = numpy.array(
            [WallBunch.ABSOLUTE_MAX_Z] * self._CLIP_WIDTH
        ).astype('float32')
        self._camera_collection = camera_collection
        self._transformation_matrix = core.Mat4.translate_mat(
            -sector_offset.x,
            -sector_offset.y,
            0
        ) * self._camera_collection.get_clipping_transform()
        self._visible_sectors: typing.Set[EditorSector] = set()
        self._sector_offset = sector_offset

        self._clipping_debug = clipping_debug
        if constants.PORTALS_DEBUGGING_ENABLED:
            self._inverse_transformation_matrix = core.Mat4()
            self._inverse_transformation_matrix.invert_from(
                self._transformation_matrix)

            self._clip_view: core.NodePath = self._clipping_debug.attach_new_node(
                'clip_view')
            self._clip_view.set_transparency(True)
            self._clip_view.set_bin('fixed', constants.FRONT_MOST)

            self._clip_card_maker = core.CardMaker('clip_view')
            self._clip_buffer_colours = numpy.array(
                [[0, 0, 0]] * self._CLIP_WIDTH
            ).astype('float32')

            self._debug_colour_index = 0
            self._debug_geometry_node = core.GeomNode('clipper')
            self._debug_geometry: core.NodePath = self._clipping_debug.attach_new_node(
                self._debug_geometry_node
            )
            self._debug_geometry.set_depth_write(False)
            self._debug_geometry.set_depth_test(False)
            self._debug_geometry.set_bin('fixed', constants.FRONT_MOST)
            self._debug_geometry.set_transparency(True)

            inverse_projection = core.Mat4().invert_from(self._transformation_matrix)

    @property
    def visible_sectors(self):
        return self._visible_sectors

    def clip(self):
        self._do_clip(self._start_sector)
        self._debug_clipped_regions()

    def _debug_clipped_regions(self):
        if not constants.PORTALS_DEBUGGING_ENABLED:
            return

        empty_colour = numpy.array([0, 0, 0])
        previous_colour = empty_colour

        left = WallBunch.ABSOLUTE_MIN_X
        right = WallBunch.ABSOLUTE_MIN_X
        for colour_index, colour in enumerate(self._clip_buffer_colours):
            if (colour != previous_colour).any():
                right = self._clip_index_to_clip_range(colour_index)
                if (previous_colour != empty_colour).any():
                    self._draw_debug_clip(previous_colour, left, right)
                left = right
            previous_colour = colour

        if right <= left and (previous_colour != empty_colour).any():
            right = self._clip_index_to_clip_range(self._CLIP_WIDTH - 1)
            self._draw_debug_clip(previous_colour, left, right)

    def _draw_debug_clip(self, colour, left: float, right: float):
        depth = 0.95

        builder_pos = self._camera_collection.get_builder_position()

        screen_left = core.Point3(left, 0, depth)
        left_3d = self._inverse_transformation_matrix.xform_point_general(
            screen_left)
        left_3d.z = builder_pos.z

        screen_right = core.Point3(right, 0, depth)
        right_3d = self._inverse_transformation_matrix.xform_point_general(
            screen_right)
        right_3d.z = builder_pos.z

        z_offset = core.Vec3(0, 0, -1024)
        self._clip_card_maker.set_frame(
            left_3d - z_offset,
            right_3d - z_offset,
            right_3d + z_offset,
            left_3d + z_offset,
        )
        self._clip_card_maker.set_color(*colour, 0.5)
        self._clip_view.attach_new_node(self._clip_card_maker.generate())

    def get_clipped_regions(self):
        in_clip = False
        left = 0
        right = 0

        regions: typing.Tuple[float, float] = []
        for index, value in enumerate(self._clip_buffer):
            if in_clip and value == WallBunch.ABSOLUTE_MAX_Z:
                in_clip = False
                right = index - 1
                regions.append(
                    (
                        self._clip_index_to_clip_range(left),
                        self._clip_index_to_clip_range(right)
                    )
                )

            elif not in_clip and value < WallBunch.ABSOLUTE_MAX_Z:
                in_clip = True
                left = index

        if in_clip:
            regions.append(
                (
                    self._clip_index_to_clip_range(left),
                    WallBunch.ABSOLUTE_MAX_X
                )
            )

        return regions

    def get_drawable_regions(self):
        in_drawable = False
        left = 0
        right = 0

        regions: typing.Tuple[float, float] = []
        for index, value in enumerate(self._clip_buffer):
            if in_drawable and value < WallBunch.ABSOLUTE_MAX_Z:
                in_drawable = False
                right = index - 1
                regions.append(
                    (
                        self._clip_index_to_clip_range(left),
                        self._clip_index_to_clip_range(right)
                    )
                )

            elif not in_drawable and value == WallBunch.ABSOLUTE_MAX_Z:
                in_drawable = True
                left = index

        if in_drawable:
            regions.append(
                (
                    self._clip_index_to_clip_range(left),
                    WallBunch.ABSOLUTE_MAX_X
                )
            )

        return regions

    def _do_clip(self, sector: EditorSector, depth=0):
        if sector in self._visible_sectors:
            return

        if depth >= self._MAX_DEPTH:
            raise AssertionError('In too deep!')

        self._visible_sectors.add(sector)
        sector.set_draw_offset(self._sector_offset)

        walls = {
            wall: ProjectedWall(wall, self._project_point)
            for wall in sector.walls
        }

        for wall in walls.values():
            wall.previous_wall = walls[wall.wall.wall_previous_point]
            wall.next_wall = walls[wall.wall.wall_point_2]

        sorted_walls: typing.List[ProjectedWall] = sorted(
            walls.values(),
            key=self._wall_distance
        )
        seen: typing.Set[ProjectedWall] = set()
        bunches: typing.List[WallBunch] = []

        for wall in sorted_walls:
            if wall in seen or self._wall_completely_invisible(wall):
                continue

            seen.add(wall)

            bunch = WallBunch(wall)
            bunches.append(bunch)

            previous_wall = wall.previous_wall
            while bunch.add_wall_previous(previous_wall):
                seen.add(previous_wall)
                previous_wall = previous_wall.previous_wall

            next_wall = wall.next_wall.next_wall
            while bunch.add_wall_next(next_wall):
                seen.add(next_wall.previous_wall)
                next_wall = next_wall.next_wall

        self._debug_sector(sector, depth)

        next_sectors = set()
        for bunch in bunches:
            if bunch.left >= bunch.right:
                continue

            start_index = self._clip_range_to_clip_index(bunch.left)
            end_index = self._clip_range_to_clip_index(bunch.right)

            partial_buffer = self._clip_buffer[start_index:end_index+1]
            visible = (partial_buffer >= bunch.depth).any()

            self._debug_bunch(bunch, visible, depth)

            if visible:
                if bunch.other_side_sector is None:
                    self._clip_buffer[start_index:end_index+1] = bunch.depth
                else:
                    next_sectors.add(bunch.other_side_sector)

        for editor_sector in next_sectors:
            self._do_clip(editor_sector, depth + 1)

        if sector.can_see_below and sector.sector_below_floor is not None:
            ror_clipper = ViewClipping(
                sector.sector_below_floor,
                self._camera_collection,
                self._clipping_debug,
                self._sector_offset + sector.get_above_draw_offset()
            )
            ror_clipper._visible_sectors = self._visible_sectors
            ror_clipper.clip()

        if sector.can_see_above and sector.sector_above_ceiling is not None:
            ror_clipper = ViewClipping(
                sector.sector_above_ceiling,
                self._camera_collection,
                self._clipping_debug,
                self._sector_offset + sector.get_below_draw_offset()
            )
            ror_clipper._visible_sectors = self._visible_sectors
            ror_clipper.clip()

    @property
    def _debug_colour(self):
        return self._BUNCH_COLOURS[self._debug_colour_index]

    def _increment_debug_colour(self):
        self._debug_colour_index = (
            self._debug_colour_index + 1) % len(self._BUNCH_COLOURS)

    def _debug_sector(self, sector: EditorSector, depth: int):
        if self._can_debug(depth):
            for editor_wall in sector.walls:
                self._debug_wall(editor_wall, 4, core.Vec4(0, 1, 0, 0.5))

                offset_2d = editor_wall.get_normalized_direction() * 2048
                offset = core.Vec3(offset_2d.x, offset_2d.y, 0) + \
                    core.Vec3(0, 0, -256)

                position = editor_wall.get_centre() - offset
                position_2 = editor_wall.get_centre() + offset

                theta = editor_wall.get_direction_theta() + 180

                self._debug_wall_projection(
                    editor_wall,
                    theta,
                    position,
                    core.Vec4(1, 0, 0, 1)
                )
                self._debug_wall_projection(
                    editor_wall.wall_point_2,
                    theta,
                    position_2,
                    core.Vec4(0, 0, 1, 1)
                )

    def _debug_bunch(self, bunch: WallBunch, visible: bool, depth: int):
        if self._can_debug(depth):
            colour = self._debug_colour
            self._increment_debug_colour()

            if visible and bunch.other_side_sector is None:
                start_index = self._clip_range_to_clip_index(bunch.left)
                end_index = self._clip_range_to_clip_index(bunch.right)
                self._clip_buffer_colours[start_index:end_index+1] = [
                    colour.x,
                    colour.y,
                    colour.z
                ]

            if len(bunch.editor_walls) > 0:
                origin = bunch.editor_walls[0].origin
                theta = bunch.editor_walls[0].get_direction_theta() + 180
                self._draw_triangle(origin, colour)

                position = origin + core.Vec3(0, 0, -512)
                self._make_debug_text(f'Visible: {visible}', position, colour, theta)

                for editor_wall in bunch.editor_walls:
                    self._debug_wall(editor_wall, 100, colour)

    @staticmethod
    def _can_debug(depth: int):
        return constants.PORTALS_DEBUGGING_ENABLED and depth >= constants.PORTAL_DEBUG_DEPTH

    def _draw_triangle(self, position: core.Point3, colour: core.Vec4):
        debug_segments = core.LineSegs('debug')
        debug_segments.set_thickness(4)
        debug_segments.set_color(colour)
        debug_segments.draw_to(position + core.Vec3(0, 1024, 0))
        debug_segments.draw_to(position + core.Vec3(1024, -1024, 0))
        debug_segments.draw_to(position + core.Vec3(-1024, -1024, 0))
        debug_segments.draw_to(position + core.Vec3(0, 1024, 0))
        debug_segments.create(self._debug_geometry_node, dynamic=False)

    def _debug_wall_projection(self, editor_wall: EditorWall, theta: float, position: core.Point3, colour: core.Vec4):
        point = self._project_point(editor_wall.point_1)

        message = f'({point.x}, {point.z})\n'
        message += f'{self._clip_range_to_clip_index(point.x)}'

        self._make_debug_text(message, position, colour, theta)

    def _make_debug_text(self, message: str, position: core.Point3, colour: core.Vec4, theta: float):
        node_name = str(uuid.uuid4())

        text_node = core.TextNode(node_name)
        text_node.set_text(message)
        text_node.set_align(core.TextNode.A_center)
        text: core.NodePath = self._debug_geometry.attach_new_node(text_node)
        text.set_color(colour)
        text.set_pos(position)
        text.set_h(theta)
        text.set_scale(-192)

    def _debug_wall(self, editor_wall: EditorWall, thickness: float, colour: core.Vec4):
        debug_segments = core.LineSegs('debug')
        debug_segments.set_thickness(thickness)
        debug_segments.set_color(colour)
        debug_segments.draw_to(editor_wall.origin)
        debug_segments.draw_to(editor_wall.wall_point_2.origin)
        debug_segments.create(self._debug_geometry_node, dynamic=False)

    def _project_point(self, point: core.Point2) -> core.Point3:
        point_3d = core.Point3(
            point.x + self._sector_offset.x,
            point.y + self._sector_offset.y,
            0
        )
        result = self._transformation_matrix.xform_point_general(point_3d)
        if result.z >= WallBunch.ABSOLUTE_MAX_Z:
            if result.x > 0:
                result.x = -constants.REALLY_BIG_NUMBER
            else:
                result.x = constants.REALLY_BIG_NUMBER

        return result

    @staticmethod
    def _clip_index_to_clip_range(value: int):
        value = ((WallBunch.WIDTH_RANGE * value) /
                 ViewClipping._CLIP_WIDTH + WallBunch.ABSOLUTE_MIN_X)
        if value < WallBunch.ABSOLUTE_MIN_X:
            return WallBunch.ABSOLUTE_MIN_X
        if value > WallBunch.ABSOLUTE_MAX_X:
            return WallBunch.ABSOLUTE_MAX_X
        return value

    @staticmethod
    def _clip_range_to_clip_index(value: int):
        value = int(((value - WallBunch.ABSOLUTE_MIN_X) /
                     WallBunch.WIDTH_RANGE) * ViewClipping._CLIP_WIDTH)
        if value < 0:
            return 0
        if value >= ViewClipping._CLIP_WIDTH:
            return ViewClipping._CLIP_WIDTH - 1
        return value

    @staticmethod
    def _wall_completely_invisible(wall: ProjectedWall):
        behind_camera = wall.point_1.z >= WallBunch.ABSOLUTE_MAX_Z and wall.point_2.z >= WallBunch.ABSOLUTE_MAX_Z
        too_far_left = wall.point_1.x <= WallBunch.ABSOLUTE_MIN_X and wall.point_2.x <= WallBunch.ABSOLUTE_MIN_X
        too_far_right = wall.point_1.x >= WallBunch.ABSOLUTE_MAX_X and wall.point_2.x >= WallBunch.ABSOLUTE_MAX_X
        return behind_camera or too_far_left or too_far_right

    @staticmethod
    def _wall_distance(wall: ProjectedWall):
        return wall.point_1.z
