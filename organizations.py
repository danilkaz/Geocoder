import sqlite3
import os
from reverse_geocoder import ReverseGeocoder
from geocoder import Geocoder

def get_info_with_organizations(city, info):
    connection = sqlite3.connect(os.path.join('db', f'{city}.db'))
    cursor = connection.cursor()

    lat, lon = info['coordinates']

    south, north = lat - 0.0025, lat + 0.0025
    west, east = lon - 0.0025, lon + 0.0025

    nodes_columns = Geocoder.get_columns(cursor, 'nodes')
    cursor.execute(
        f"SELECT * FROM nodes WHERE "
        f"(lat BETWEEN {south} AND {north}) AND"
        f"(lon BETWEEN {west} AND {east}) AND "
        f"(NOT(name IS NULL) OR NOT(shop IS NULL) "
        f"OR NOT(amenity IS NULL))")
    organizations = zip_elements(nodes_columns, cursor.fetchall())

    ways_columns = Geocoder.get_columns(cursor, 'ways')
    cursor.execute(f"SELECT * FROM ways WHERE"
                   f"(lat BETWEEN {south} AND {north}) AND "
                   f"(lon BETWEEN {west} AND {east}) AND "
                   f"(NOT(name IS NULL) OR NOT(shop IS NULL) OR NOT(amenity IS NULL))")
    organizations += zip_elements(ways_columns, cursor.fetchall())

    info['organizations'] = []

    for organization in organizations:
        if ReverseGeocoder.is_point_in_polygon([organization['lat'], organization['lon']], info['nodes']):
            info['organizations'].append(organization)
    return info

def zip_elements(columns, organizations):
    result = []
    for organization in organizations:
        d = dict()
        for elem in zip(columns, organization):
            if elem[1] is not None:
                d[elem[0]] = elem[1]
        result.append(d)
    return result
