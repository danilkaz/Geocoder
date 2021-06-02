import sqlite3
import os
from extensions import get_nodes, normalize_string_sqlite, get_average_point


def do_geocoding(city, street, house_number):
    connection = sqlite3.connect(os.path.join('db', f'{city}.db'))
    connection.create_function('NORMALIZE', 1, normalize_string_sqlite)
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM ways "
                   f"WHERE (NORMALIZE([addr:street]) LIKE "
                   f"'%{normalize_string_sqlite(street)}%') "
                   f"AND (NORMALIZE([addr:housenumber]) = "
                   f"'{normalize_string_sqlite(house_number)}')")
    result = cursor.fetchall()

    columns = get_columns(cursor, 'ways')

    result = list(map(lambda adr: dict(zip(columns, adr)), result))
    result = remove_info_repeats(result)

    if len(result) == 0:
        print('Данный адрес не найден. Проверьте правильность ввода.')
        exit(1)
    if len(result) > 1:
        print('Найдено больше одного адреса. Уточните запрос.')
        for i, info in enumerate(result):
            print(f"{i + 1}) "
                  f"{info['addr:street']} {info['addr:housenumber']}")
        exit(2)
    connection.close()
    return get_new_info(result[0])


def remove_info_repeats(array):
    s = set()
    for info in array[:]:
        t = (info['addr:street'], info['addr:housenumber'])
        if t in s:
            array.remove(info)
        s.add(t)
    return array


def get_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    columns = list(map(lambda x: x[1], cursor.fetchall()))
    return columns


def get_new_info(info):
    new_info = dict()

    nodes = get_nodes(info['nodes'])
    str_points = list(map(lambda p: p.split(', '), nodes))
    points = list(map(lambda p: [float(p[0]), float(p[1])], str_points))
    average_point = get_average_point(points)

    for item in info.items():
        if item[1] is not None and item[0] != 'nodes':
            new_info[str(item[0])] = str(item[1])
    new_info['nodes'] = list(map(tuple, points))
    new_info['coordinates'] = average_point
    return new_info
