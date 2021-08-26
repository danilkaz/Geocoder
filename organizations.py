import os
import sqlite3
from typing import Any

from direct_geocoder import get_table_columns
from reverse_geocoder import is_point_in_polygon
from utils import zip_table_columns_with_table_rows, get_average_point


def get_organizations_by_address_border(city: str,
                                        nodes: list[tuple[float, float]]) \
        -> list[dict[str, Any]]:
    result = []
    radius = 0.0025
    with sqlite3.connect(os.path.join('db', f'{city}.db')) as connection:
        cursor = connection.cursor()
        lat, lon = get_average_point(nodes)
        south, north = lat - radius, lat + radius
        west, east = lon - radius, lon + radius
        request_template = f"SELECT * FROM nodes WHERE " \
                           f"(lat BETWEEN ? AND ?) AND " \
                           f"(lon BETWEEN ? AND ?) AND " \
                           f"(highway IS NULL) AND" \
                           f"(NOT(name IS NULL) OR " \
                           f"NOT(shop IS NULL) OR " \
                           f"NOT(amenity IS NULL))"
        organizations_within_radius = []
        nodes_columns = get_table_columns(cursor, 'nodes')
        ways_columns = get_table_columns(cursor, 'ways')
        cursor.execute(request_template, (south, north, west, east))
        organizations_within_radius += zip_table_columns_with_table_rows(
            nodes_columns,
            cursor.fetchall())
        request_template = request_template.replace('nodes', 'ways')
        cursor.execute(request_template, (south, north, west, east))
        organizations_within_radius += zip_table_columns_with_table_rows(
            ways_columns,
            cursor.fetchall())
    for organization in organizations_within_radius:
        if is_point_in_polygon((organization['lat'], organization['lon']),
                               nodes):
            result.append(organization)
    return result
