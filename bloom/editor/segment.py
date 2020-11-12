import math

from panda3d import core

from .. import editor


class Segment:

    def __init__(self, point_1: core.Point2, point_2: core.Point2):
        self._point_1 = point_1
        self._point_2 = point_2

    @property
    def point_1(self):
        return self._point_1

    @property
    def point_2(self):
        return self._point_2

    @property
    def is_empty(self):
        direction = self.get_direction()
        return direction.x == 0 and direction.y == 0

    def get_centre(self) -> core.Point2:
        return (self._point_1 + self._point_2) / 2

    def side_of_line(self, point: core.Point2):
        return editor.side_of_line(point, self._point_1, self._point_2)

    def get_normal(self) -> core.Vec2:
        return self.get_orthogonal_vector().normalized()

    def get_orthogonal_vector(self) -> core.Vec2:
        direction = self.get_direction()
        return core.Vec2(direction.y, -direction.x)

    def get_direction(self) -> core.Vec2:
        return self._point_2 - self._point_1

    def get_direction_theta(self) -> float:
        direction = self.get_direction()
        theta = math.atan2(direction.y, direction.x)
        return math.degrees(theta)

    def get_normalized_direction(self) -> core.Vec2:
        return self.get_direction().normalized()

    def segment_within(self, other: 'Segment') -> 'Segment':
        if self.is_empty:
            return None

        if self.side_of_line(other._point_1) == 0 and \
                self.side_of_line(other._point_2) == 0:
            direction = self.get_direction()
            is_more_vertical = math.fabs(direction.y) > math.fabs(direction.x)

            point_1_delta = other._point_1 - self._point_1
            point_2_delta = other._point_2 - self._point_1

            if is_more_vertical:
                portion_1 = point_1_delta.y / direction.y
                portion_2 = point_2_delta.y / direction.y
                if portion_1 >= 0 and portion_1 <= 1:
                    point_1_intersect = other._point_1
                    if portion_2 >= 0 and portion_2 <= 1:
                        point_2_intersect = other._point_2
                    else:
                        point_2_intersect = self._point_2
                elif portion_2 >= 0 and portion_2 <= 1:
                    point_1_intersect = self._point_1
                    point_2_intersect = other._point_2
                else:
                    return None
            else:
                portion_1 = point_1_delta.x / direction.x
                portion_2 = point_2_delta.x / direction.x
                if portion_1 >= 0 and portion_1 <= 1:
                    point_1_intersect = other._point_1
                    if portion_2 >= 0 and portion_2 <= 1:
                        point_2_intersect = other._point_2
                    else:
                        point_2_intersect = self._point_2
                elif portion_2 >= 0 and portion_2 <= 1:
                    point_1_intersect = self._point_1
                    point_2_intersect = other._point_2
                else:
                    return None

            return Segment(point_1_intersect, point_2_intersect)

        return None

    def point_on_line(self, point: core.Point2):
        if self.is_empty or self.side_of_line(point) != 0:
            return False

        delta = point - self.point_1
        direction = self.get_direction()
        is_more_vertical = math.fabs(direction.y) > math.fabs(direction.x)

        if is_more_vertical:
            portion = delta.y / direction.y
            return portion >= 0 and portion <= 1

        portion = delta.x / direction.x
        return portion >= 0 and portion <= 1

    def intersect_line(self, point: core.Point2, direction: core.Vec2):
        point_on_line = point + direction
        if self.side_of_line(point) <= 0:
            facing = direction.dot(self.get_orthogonal_vector())
            if facing >= 0:
                segment_side_of_line_point_1 = editor.side_of_line(
                    self._point_1, 
                    point, 
                    point_on_line
                )
                
                segment_side_of_line_point_2 = editor.side_of_line(
                    self._point_2, 
                    point, 
                    point_on_line
                )

                if segment_side_of_line_point_1 != segment_side_of_line_point_2:
                    return editor.line_intersection(
                        point, point_on_line,
                        self._point_1, self._point_2
                    )
        return None
