import os
import sqlite3
from typing import Iterable, Any

import json
from answer import GeocoderAnswer
from utils import normalize_string_sqlite, get_average_point


def do_geocoding(city: str,
                 street: str,
                 house_number: str) -> GeocoderAnswer:
    with sqlite3.connect(os.path.join('db', f'{city}.db')) as connection:
        connection.create_function('NORMALIZE', 1, normalize_string_sqlite)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM ways "
                       "WHERE (NORMALIZE([addr:street]) "
                       "LIKE '%' || ? || '%')"
                       "AND (NORMALIZE([addr:housenumber]) = ?)",
                       (normalize_string_sqlite(street),
                        normalize_string_sqlite(house_number)))
        result = cursor.fetchall()
    columns = get_table_columns(cursor, 'ways')
    result = map(lambda address: dict(zip(columns, address)), result)
    result = remove_duplicates_from_potential_answers_list(result)
    if len(result) == 0:
        print('Данный адрес не найден. Проверьте правильность ввода.')
        exit(1)
    if len(result) > 1:
        print('Найдено больше одного адреса. Уточните запрос.')
        # TODO майская первомайская
        for i, info_from_db in enumerate(result):
            print(f"{i + 1}) "
                  f"{info_from_db['addr:street']} "
                  f"{info_from_db['addr:housenumber']}")
        exit(2)
    return form_geocoder_answer(result[0])


def get_table_columns(cursor: sqlite3.Cursor, table_name: str) -> list[str]:
    """Получение всех столбцов для оалдыв ошадва оо ацддд одло щво"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = list(map(lambda x: x[1], cursor.fetchall()))
    return columns


def remove_duplicates_from_potential_answers_list(answers: Iterable) \
        -> list[dict[str, Any]]:
    addresses = set()
    result = []
    for potential_answer in answers:
        address = (potential_answer['addr:street'],
                   potential_answer['addr:housenumber'])
        if address in addresses:
            continue
        addresses.add(address)
        result.append(potential_answer)
    return result


def form_geocoder_answer(info_from_db: dict[str, Any]) -> GeocoderAnswer:
    answer = GeocoderAnswer()
    # TODO try except
    answer.region = info_from_db['addr:region']
    answer.city = info_from_db['addr:city']
    answer.street = info_from_db['addr:street']
    answer.house_number = info_from_db['addr:housenumber']
    points = list(map(tuple, json.loads(info_from_db['nodes'])))
    average_point = get_average_point(points)
    answer.lat, answer.lon = average_point
    used_keys = ('addr:region',
                 'addr:city',
                 'addr:street',
                 'addr:housenumber',
                 'lat', 'lon')
    for item in filter(lambda it: it[1] and it[0] not in used_keys,
                       info_from_db.items()):
        answer.additional_information[str(item[0])] = str(item[1])
    answer.additional_information['nodes'] = points
    return answer
