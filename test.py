from math import atan2

polygon = [[56.8552892, 53.1985857], [56.8553002, 53.1987764], [56.856239, 53.1984278], [56.8562485, 53.1986188]]


def cmp_to_key(mycmp):
    'Перевести cmp=функция в key=функция'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

def get_average_point(points):
    x = 0
    y = 0
    for point in points:
        point[0], point[1] = float(point[0]), float(point[1])
        x += point[0]
        y += point[1]
    return round(x / len(points), 7), round(y / len(points), 7)

center = get_average_point(polygon)

def compare(a, b):

    if a[0] - center[0] >= 0 and b[0] - center[0] < 0:
        return True
    if a[0] - center[0] < 0 and b[0] - center[0] >= 0:
        return False
    if a[0] - center[0] == 0 and b[0] - center[0] == 0:
        if a[1] - center[1] >= 0 or b[1] - center[1] >= 0:
            return a[1] > b[1]
        return b[1] > a[0]

    det = (a[0] - center[0]) * (b[1] - center[1]) - (b[0] - center[0]) * (a[1] - center[1])
    if det < 0:
        return True
    if det > 0:
        return False
    d1 = (a[0] - center[0]) * (a[0] - center[0]) + (a[1] - center[1]) * (a[1] - center[1])

    d2 = (b[0] - center[0]) * (b[0] - center[0]) + (b[1] - center[1]) * (b[1] - center[1])
    return d1 > d2

sort_polygon = sorted(polygon, key=cmp_to_key(compare))
print(sort_polygon)
