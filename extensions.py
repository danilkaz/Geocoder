def get_nodes(nodes):
    nodes = nodes[1:-1].split('], [')
    nodes[0] = nodes[0][1:]
    nodes[-1] = nodes[-1][:-1]
    return nodes


def normalize_string_sqlite(string):
    return str(string).lower().replace(' ', '').replace('-', '')


def get_average_point(points):
    x = 0
    y = 0
    if len(points) == 0:
        return None
    for point in points:
        px, py = float(point[0]), float(point[1])
        x += px
        y += py
    return round(x / len(points), 7), round(y / len(points), 7)
