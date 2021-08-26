import os
import sqlite3

import requests
from tqdm import tqdm

from utils import normalize_string_sqlite, is_file_exist
from xml_parser import Parser


def download_city_xml(city: str) -> None:
    coordinates = get_city_coordinates(city)
    south = round(coordinates[0], 4)
    north = round(coordinates[1], 4)
    west = round(coordinates[2], 4)
    east = round(coordinates[3], 4)
    url = f"https://overpass-api.de/api/map?bbox=" \
          f"{west},{south},{east},{north}"
    print('Делаем запрос')
    response = requests.get(url, stream=True)
    print('Ответ получен. Скачиваем файл')
    bar = tqdm(desc='Скачано уже', unit='B', unit_scale=True)
    with open(os.path.join('xml', f"{city}.xml"), 'wb') as f:
        for chunk in response.iter_content(chunk_size=10 * 1024 * 1024):
            if chunk:
                bar.update(1024 * 10 * 8)
                f.write(chunk)
        bar.close()


def get_city_coordinates(city: str) -> tuple[int]:
    with sqlite3.connect(os.path.join('db', 'cities.db')) as connection:
        connection.create_function('NORMALIZE', 1, normalize_string_sqlite)
        cursor = connection.cursor()
        cursor.execute(f"SELECT south, north, west, east "
                       f"FROM cities "
                       f"WHERE NORMALIZE(city) IN "
                       f"('{normalize_string_sqlite(city)}')")
        coordinates = cursor.fetchone()
        if not coordinates:
            print('Такого города в базе нет.')
            exit(3)
    return coordinates


def get_base(city: str) -> None:
    if not is_file_exist(f'{city}.db', os.path.join('db')):
        if not is_file_exist(f'{city}.xml', os.path.join('xml')):
            download_city_xml(city)
        parser = Parser(city)
        parser.parse()
