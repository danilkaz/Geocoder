import math
import sqlite3
import os
from extensions import get_nodes
from direct_geocoder import do_geocoding


def do_reverse_geocoding(lat, lon, city):
    connection = sqlite3.connect(os.path.join('db', f"{city}.db"))
    cursor = connection.cursor()

    south, north = lat - 0.004, lat + 0.004
    west, east = lon - 0.004, lon + 0.004

    info = get_info_from_square(cursor, south, north, west, east)
    for elem in info:
        nodes = get_nodes(elem[1])
        nodes = map(lambda x: x.split(', '), nodes)
        nodes = list(map(lambda x: (float(x[0]), float(x[1])), nodes))
        if is_point_in_polygon((lat, lon), nodes):
            return do_geocoding(city, elem[2], elem[3])
    else:
        south, north = lat - 0.00025, lat + 0.00025
        west, east = lon - 0.00025, lon + 0.00025
        info = get_info_from_square(cursor, south, north, west, east)
        result = []
        for elem in info:
            result.append((elem[2], elem[3]))

        if len(result) == 0:
            print('Ничего не найдено')
            exit(8)
        if len(result) > 1:
            print('Найдено несколько результатов')
            for i, info in enumerate(result):
                print(f"{i + 1}) {result[i][0]} {result[i][1]}")
            exit(9)
        return do_geocoding(city, result[0][0], result[0][1])


def is_point_in_polygon(point, polygon):
    delta = [0.00005, -0.00005, 0]
    points = []
    for dx in delta:
        for dy in delta:
            points.append([point[0] + dx, point[1] + dy])
    n = len(polygon)
    for point in points:
        angle = 0
        for i in range(n):
            side1 = (polygon[i][0] - point[0],
                     polygon[i][1] - point[1])
            side2 = (polygon[(i + 1) % n][0] - point[0],
                     polygon[(i + 1) % n][1] - point[1])
            angle += math.atan2(cross(side1, side2), dot(side1, side2))
        if abs(abs(angle) - 2 * math.pi) < 0.1:
            return True
    return False


def get_info_from_square(cursor, south, north, west, east):
    sql_request = "SELECT id, nodes, [addr:street], [addr:housenumber] " \
                  "FROM ways " \
                  "WHERE (lat BETWEEN ? AND ?) " \
                  "AND (lon BETWEEN ? AND ?) " \
                  "AND NOT (nodes IS NULL) " \
                  "AND NOT ([addr:street] IS NULL) " \
                  "AND NOT ([addr:housenumber] IS NULL)"
    cursor.execute(sql_request, (south, north, west, east))
    return cursor.fetchall()


def find_city(lat, lon):
    connection = sqlite3.connect(os.path.join('db', 'cities.db'))
    cursor = connection.cursor()

    cursor.execute(f"SELECT city, region FROM cities "
                   f"WHERE ({lat} BETWEEN south AND north) "
                   f"AND ({lon} BETWEEN west AND east)")
    info = cursor.fetchall()
    if len(info) == 0:
        print('Данная точка не находится в городе')
        exit(6)
    return info[0]


def dot(point1, point2):
    return point1[0] * point2[0] + point1[1] * point2[1]


def cross(point1, point2):
    return point1[0] * point2[1] - point1[1] * point2[0]
