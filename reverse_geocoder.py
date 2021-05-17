import math
import sqlite3
import os


def get_objects_binsearch(lat, lon, city):
    connection = sqlite3.connect(os.path.join('db', f"{city}.db"))
    cursor = connection.cursor()

    left_border = 0.0001
    right_border = 0.002
    while abs(left_border - right_border) > 0.000001:
        middle = (left_border + right_border) / 2
        #print(middle)
        south, north = lat - middle, lat + middle
        west, east = lon - middle, lon + middle

        cursor.execute( f"SELECT id, nodes, [addr:street], [addr:housenumber] FROM ways WHERE ([coordinateX] BETWEEN {south} AND {north}) AND"
                        f"([coordinateY] BETWEEN {west} AND {east}) AND NOT([addr:street] IS NULL) AND NOT(nodes IS null) AND "
                        f"NOT([addr:housenumber] IS NULL)")
        info = cursor.fetchall()
        if len(info) == 1:
            #print(info[0][2], info[0][3])
            return info[0][2], info[0][3]
        elif len(info) > 1:
            right_border = middle
        else:
            left_border = middle


def get_objects(lat, lon, city):
    connection = sqlite3.connect(os.path.join('db', f"{city}.db"))
    cursor = connection.cursor()

    south, north = lat - 0.004, lat + 0.004
    west, east = lon - 0.004, lon + 0.004

    cursor.execute(f"SELECT id, nodes, [addr:street], [addr:housenumber] FROM ways WHERE ([coordinateX] BETWEEN {south} AND {north}) AND"
                   f"([coordinateY] BETWEEN {west} AND {east}) AND NOT([addr:street] IS NULL) AND NOT(nodes IS null) AND "
                   f"NOT([addr:housenumber] IS NULL)")
    info = cursor.fetchall()
    for elem in info:
        nodes = get_nodes(elem[1])
        nodes = map(lambda x: x.split(', '), nodes)
        nodes = list(map(lambda x: (float(x[0]), float(x[1])), nodes))
        if 'Горького' in elem[2] and elem[3] == '156':
            print(nodes)
        if is_point_in_polygon((lat, lon), nodes):
            print(city, elem[2], elem[3])
            break
    else:
        print('я тут')
        south, north = lat - 0.00025, lat + 0.00025
        west, east = lon - 0.00025, lon + 0.00025
        cursor.execute(
            f"SELECT id, nodes, [addr:street], [addr:housenumber] FROM ways WHERE ([coordinateX] BETWEEN {south} AND {north}) AND"
            f"([coordinateY] BETWEEN {west} AND {east}) AND NOT([addr:street] IS NULL) AND NOT(nodes IS null) AND "
            f"NOT([addr:housenumber] IS NULL)")
        info = cursor.fetchall()
        for elem in info:
            print(elem[2], elem[3])


def get_nodes(nodes):
    nodes = nodes[1:-1].split('], [')
    nodes[0] = nodes[0][1:]
    nodes[-1] = nodes[-1][:-1]
    return nodes


def is_point_in_polygon(point, polygon):
    n = len(polygon)
    angle = 0
    polygon = polygon[::-1]
    for i in range(n):
        side1 = (polygon[i][0] - point[0], polygon[i][1] - point[1])
        side2 = (polygon[(i + 1) % n][0] - point[0], polygon[(i + 1) % n][1] - point[1])
        angle += math.atan2(cross(side1, side2), dot(side1, side2))
    if abs(abs(angle) - 2 * math.pi) < 0.1:
        return True
    return False


def dot(point1, point2):
    return point1[0] * point2[0] + point1[1] * point2[1]


def cross(point1, point2):
    return point1[0] * point2[1] - point1[1] * point2[0]