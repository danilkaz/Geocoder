import os
import sqlite3
from typing import Optional, Iterable, Any

from answer import GeocoderAnswer


def get_nodes(nodes):
    nodes = nodes[1:-1].split('], [')
    nodes[0] = nodes[0][1:]
    nodes[-1] = nodes[-1][:-1]
    return nodes


def zip_table_columns_with_table_rows(columns: Iterable[str],
                                      rows: Iterable[Iterable[Any]]) \
        -> list[dict[str, Any]]:
    result = []
    for row in rows:
        d = dict()
        for elem in zip(columns, row):
            if elem[1]:
                d[elem[0]] = elem[1]
        result.append(d)
    return result


def get_fixed_city_and_region_name(city: str) -> tuple[str, str]:
    with sqlite3.connect(os.path.join('db', 'cities.db')) as connection:
        connection.create_function('NORMALIZE', 1, normalize_string_sqlite)
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT city, region FROM cities "
            f"WHERE NORMALIZE(city) IN (?)",
            (normalize_string_sqlite(city),)
        )
        answer = cursor.fetchone()
        if not answer:
            print('Введенный город не найден')
            exit(12)
    city, region = answer
    return city, region


def find_city_and_region(lat: float, lon: float) -> tuple[str, str]:
    with sqlite3.connect(os.path.join('db', 'cities.db')) as connection:
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT city, region FROM cities "
            f"WHERE (? BETWEEN south AND north) "
            f"AND (? BETWEEN west AND east)",
            (lat, lon)
        )
        answer = cursor.fetchone()
        if not answer:
            print('Данная точка не находится в городе')
            exit(5)
    city, region = answer
    return city, region


def check_and_update_city_and_region(answer: GeocoderAnswer,
                                     region: str,
                                     city: str) -> GeocoderAnswer:
    if answer.region is None:
        answer.region = region
    if answer.city is None:
        answer.city = city
    return answer


def normalize_string_sqlite(string: str) -> str:
    return str(string).lower().replace(' ', '').replace('-', '')


def get_average_point(points: list[tuple[float, float]]
                      ) -> Optional[tuple[float, float]]:
    x = 0
    y = 0
    if len(points) == 0:
        return None
    for point in points:
        px, py = float(point[0]), float(point[1])
        x += px
        y += py
    return round(x / len(points), 7), round(y / len(points), 7)


def create_directories() -> None:
    if not is_directory_exist('xml', os.path.curdir):
        os.mkdir('xml')
    if not is_directory_exist('json', os.path.curdir):
        os.mkdir('json')


def is_file_exist(file_name: str, path: str) -> bool:
    for root, dirs, files in os.walk(path):
        if file_name in files:
            return True
    return False


def is_directory_exist(directory_name: str, path: str) -> bool:
    for root, dirs, files in os.walk(path):
        if directory_name in dirs:
            return True
    return False
