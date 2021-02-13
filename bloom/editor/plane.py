from panda3d import core


class Plane:
    def __init__(
        self, point_1: core.Point3, point_2: core.Point3, point_3: core.Point3
    ):
        self._point_1 = point_1
        self._point_2 = point_2
        self._point_3 = point_3

    def get_orthonal(self) -> core.Vec3:
        direction_1 = self._point_2 - self._point_1
        direction_2 = self._point_3 - self._point_1
        return direction_1.cross(direction_2)

    def get_normal(self) -> core.Vec3:
        return self.get_orthonal().normalized()

    def intersect_line(self, point: core.Point3, direction: core.Vec3) -> core.Point3:
        normal = self.get_normal()
        divisor = direction.dot(normal)

        if divisor == 0:
            return None

        line_portion = (self._point_1 - point).dot(normal) / divisor
        return point + direction * line_portion
