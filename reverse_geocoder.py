import math
import os
import sqlite3
from typing import Any

import json
from answer import GeocoderAnswer
from direct_geocoder import do_geocoding
from utils import zip_table_columns_with_table_rows


def do_reverse_geocoding(city: str,
                         lat: float,
                         lon: float) -> GeocoderAnswer:
    south, north = lat - 0.004, lat + 0.004
    west, east = lon - 0.004, lon + 0.004
    addresses_with_nodes = \
        get_all_addresses_from_square(city, south, north, west, east)
    for address in addresses_with_nodes:
        nodes = list(map(tuple, json.loads(address['nodes'])))
        if is_point_in_polygon((lat, lon), nodes):
            return do_geocoding(city,
                                address['addr:street'],
                                address['addr:housenumber'])
    else:
        south, north = lat - 0.00025, lat + 0.00025
        west, east = lon - 0.00025, lon + 0.00025
        addresses_with_nodes = \
            get_all_addresses_from_square(city, south, north, west, east)
        result = []
        for address in addresses_with_nodes:
            result.append(
                (address['addr:street'], address['addr:housenumber'])
            )
        if len(result) == 0:
            print('Ничего не найдено')
            exit(8)
        if len(result) > 1:
            print('Найдено несколько результатов')
            for i, addresses_with_nodes in enumerate(result):
                print(f"{i + 1}) {result[i][0]} {result[i][1]}")
            exit(9)
        street = result[0][0]
        house_number = result[0][1]
        return do_geocoding(city, street, house_number)


def get_all_addresses_from_square(city: str,
                                  south: float,
                                  north: float,
                                  west: float,
                                  east: float) -> list[dict[str, Any]]:
    with sqlite3.connect(os.path.join('db', f'{city}.db')) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT nodes, [addr:street], [addr:housenumber] "
                       "FROM ways "
                       "WHERE (lat BETWEEN ? AND ?) "
                       "AND (lon BETWEEN ? AND ?) "
                       "AND NOT (nodes IS NULL) "
                       "AND NOT ([addr:street] IS NULL) "
                       "AND NOT ([addr:housenumber] IS NULL)",
                       (south, north, west, east))
        addresses_with_nodes = \
            zip_table_columns_with_table_rows(
                ('nodes', 'addr:street', 'addr:housenumber'),
                cursor.fetchall())
        return addresses_with_nodes


def is_point_in_polygon(point: tuple[float, float],
                        polygon: list[tuple[float, float]]):
    """
    Проверка точки на принадлежность многоугольнику.

    """
    delta = [0.00005, -0.00005, 0]
    points = []
    for dx in delta:
        for dy in delta:
            points.append([point[0] + dx, point[1] + dy])
    for point in points:
        angle = 0
        for i in range(len(polygon)):
            side1 = (polygon[i][0] - point[0],
                     polygon[i][1] - point[1])
            side2 = (polygon[(i + 1) % len(polygon)][0] - point[0],
                     polygon[(i + 1) % len(polygon)][1] - point[1])
            angle += math.atan2(cross(side1, side2), dot(side1, side2))
        if abs(abs(angle) - 2 * math.pi) < 0.1:
            return True
    return False


def dot(point1: tuple[float, float], point2: tuple[float, float]) -> float:
    """Скалярное произведение векторов для нахождения угла между ними"""
    return point1[0] * point2[0] + point1[1] * point2[1]


def cross(point1: tuple[float, float], point2: tuple[float, float]) -> float:
    """Векторное произведение векторов для нахождения угла между ними"""
    return point1[0] * point2[1] - point1[1] * point2[0]
