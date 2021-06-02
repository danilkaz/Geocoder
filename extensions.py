import os
import sqlite3


def get_nodes(nodes):
    nodes = nodes[1:-1].split('], [')
    nodes[0] = nodes[0][1:]
    nodes[-1] = nodes[-1][:-1]
    return nodes


def get_fixed_city_and_region_name(city):
    city_conn = sqlite3.connect(os.path.join('db', 'cities.db'))
    city_conn.create_function('NORMALIZE', 1, normalize_string_sqlite)
    city_cursor = city_conn.cursor()
    city_cursor.execute(
        f"SELECT city, region FROM cities "
        f"WHERE NORMALIZE(city) IN "
        f"('{normalize_string_sqlite(city)}')"
    )
    city_info = city_cursor.fetchall()
    if len(city_info) == 0:
        print('Введенный город не найден')
        exit(12)
    city, region = city_info[0]
    city_conn.close()
    return city, region


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


def create_directories():
    if not is_directory_exist('xml', os.path.curdir):
        os.mkdir('xml')
    if not is_directory_exist('json', os.path.curdir):
        os.mkdir('json')


def is_file_exist(file_name, path):
    for root, dirs, files in os.walk(path):
        if file_name in files:
            return True
    return False


def is_directory_exist(directory_name, path):
    for root, dirs, files in os.walk(path):
        if directory_name in dirs:
            return True
    return False
