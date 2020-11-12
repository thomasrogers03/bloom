# Copyright 2020 Thomas Rogers
# SPDX-License-Identifier: Apache-2.0

import numpy
from panda3d import core


def to_degrees(build_angle: int) -> float:
    return (180 * build_angle) / 1024 - 90


def to_build_angle(degrees: float) -> int:
    return round(((degrees + 90) * 1024) / 180)


def to_height(build_height: int) -> float:
    return build_height / float(1 << 4)


def to_build_height(height: float) -> int:
    return round(height * (1 << 4))


def to_heinum(build_height: int) -> float:
    return build_height / float(1 << 12)


def to_build_heinum(height: float) -> int:
    return round(height * (1 << 12))


def to_sprite_repeat(build_sprite_repeat: int) -> float:
    return build_sprite_repeat / 4


def to_build_sprite_repeat(sprite_repeat: float) -> int:
    return round(sprite_repeat * 4)


def to_repeat_x(build_repeat_x: int) -> float:
    return build_repeat_x * 8


def to_build_repeat_x(repeat_x: float) -> int:
    return _valid_unsigned_byte(repeat_x / 8)


def to_repeat_y(build_repeat_y: int) -> float:
    return build_repeat_y / 128


def to_build_repeat_y(repeat_y: float) -> int:
    return _valid_unsigned_byte(repeat_y * 128)


def to_panning_x(panning_x: int) -> float:
    return float(panning_x)


def to_build_panning_x(panning_x: float) -> int:
    return round(panning_x)


def to_panning_y(build_panning_y: int) -> float:
    return build_panning_y / 2


def to_build_panning_y(build_panning_y: float) -> int:
    return round(build_panning_y * 2)


def to_shade(build_shade: int):
    return 1 - (build_shade / 64)


def to_build_shade(shade: float):
    return round((1 - shade) * 64)


def snap_to_grid(value: float, grid_size: float):
    return round(value / grid_size) * grid_size


def side_of_line(point: core.Point2, line_point_1: core.Point2, line_point_3: core.Point2, tolerance = 0.0):
    line_direction = line_point_3 - line_point_1
    orthogonal = core.Vec2(line_direction.y, -line_direction.x)

    relative_point = point - line_point_1
    direction = orthogonal.dot(relative_point)

    if direction > tolerance:
        return 1
    elif direction < -tolerance:
        return -1
    return 0


def line_intersection(
    segment_1_point_1: core.Point2,
    segment_1_point_2: core.Point2,
    segment_2_point_1: core.Point2,
    segment_2_point_2: core.Point2
):
    segment_1_diff = segment_1_point_1 - segment_1_point_2
    segment_2_diff = segment_2_point_1 - segment_2_point_2

    x_diff = core.Vec2(segment_1_diff.x, segment_2_diff.x)
    y_diff = core.Vec2(segment_1_diff.y, segment_2_diff.y)

    divisor = determinant(x_diff, y_diff)
    if divisor == 0:
        raise ValueError('Lines do not intersect')

    det = core.Vec2(
        determinant(segment_1_point_1, segment_1_point_2),
        determinant(segment_2_point_1, segment_2_point_2)
    )

    x = determinant(det, x_diff) / divisor
    y = determinant(det, y_diff) / divisor

    return core.Point2(x, y)


def determinant(first: core.Vec2, second: core.Vec2):
    return first.x * second.y - first.y * second.x


def _valid_unsigned_byte(value: float):
    value = round(value)

    if value > 127:
        return 127

    if value < -128:
        return -128

    return value
