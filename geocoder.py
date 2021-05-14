from xml_parser import Parser
import argparse
import sqlite3
import json
import os
import requests
from tqdm import tqdm


def main():
    if not is_directory_exist('xml', os.path.curdir):
        os.mkdir('xml')
    if not is_directory_exist('json', os.path.curdir):
        os.mkdir('json')

    argparser = argparse.ArgumentParser('Геокодер')

    argparser.add_argument('-r', '--reverse', action='store_true', help="Использовать для обратного геокодинга")
    argparser.add_argument('city', type=str, help='Название города')
    argparser.add_argument('street', type=str, help='Название улицы, проспекта и т.д')
    argparser.add_argument('house_number', type=str, help='Номер дома')
    argparser.add_argument('-j', '--json', action='store_true', help="Вывод в файл .json")
    argparser.add_argument('-a', '--additional', action='store_true', help="Получить дополнительную информации о зданни")

    args = argparser.parse_args()

    args.city = args.city.title()

    if not is_file_exist(f'{args.city}.db', os.path.join('db')):
        if not is_file_exist(f'{args.city}.xml', os.path.join('xml')):
            download_city_xml(args.city)
        parser = Parser(args.city)
        parser.parse()

    connection = sqlite3.connect(os.path.join('db', f'{args.city}.db'))
    connection.create_function('NORMALIZE', 1, normalize_string_sqlite)
    cursor = connection.cursor()

    if args.reverse:
        pass
    else:
        info = do_geocoding(cursor, args.street, args.house_number)
        city = args.city
        street = info['addr:street']
        house_number = info['addr:housenumber']
        coordinates = info['coordinates']

        if args.json:
            street = street.replace(' ', '_')
            house_number = house_number.replace(' ', '_')
            file_name = f'{city}_{street}_{house_number}.json'
            with open(os.path.join('json', file_name), 'w', encoding='utf-8') as fp:
                json.dump(info, fp, ensure_ascii=False)
            print(f'\nФайл сохранен в папку json с именем "{file_name}"')
        else:
            print(f"\nАдрес: {city}, {street}, {house_number}")
            print(f"Координаты: {coordinates}")

            if args.additional:
                print('\nДополнительная информация OpenStreetMap:')
                for key, value in info.items():
                    if key not in ['addr:city' ,'addr:street', 'addr:housenumber', 'coordinates']:
                        print(f'{key} : {value}')


def normalize_string_sqlite(string):
    return str(string).lower().replace(' ', '').replace('-', '')


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


def get_average_point(points):
    x = 0
    y = 0
    for point in points:
        point[0], point[1] = float(point[0]), float(point[1])
        x += point[0]
        y += point[1]
    return round(x / len(points), 7), round(y / len(points), 7)


def do_geocoding(cursor, street, house_number):
    cursor.execute(f"SELECT * FROM ways "
                   f"WHERE (NORMALIZE([addr:street]) LIKE '%{normalize_string_sqlite(street)}%') "
                   f"AND (NORMALIZE([addr:housenumber]) = '{normalize_string_sqlite(house_number)}')")
    result = cursor.fetchall()

    cursor.execute(f"PRAGMA table_info('ways')")
    columns = list(map(lambda x: x[1], cursor.fetchall()))

    result = list(map(lambda adr: dict(zip(columns, adr)), result))

    s = set()
    for info in result[:]:
        t = (info['addr:street'], info['addr:housenumber'])
        if t in s:
            result.remove(info)
        s.add(t)

    if len(result) == 0:
        print('Данный адрес не найден. Проверьте правильность ввода.')
        exit(1)
    if len(result) > 1:
        print('Найдено больше одного адреса. Уточните запрос.')
        for i, info in enumerate(result):
            print(f"{i+1}) {info['addr:street']} {info['addr:housenumber']}")

        exit(2)

    info = result[0]
    new_info = dict()
    nodes = get_nodes(info)
    points = list(map(lambda p: p.split(', '), nodes))
    average_point = get_average_point(points)

    for tup in info.items():
        if tup[1] is not None and tup[0] != 'nodes':
            new_info[str(tup[0])] = str(tup[1])
    new_info['nodes'] = list(map(tuple, points))
    new_info['coordinates'] = average_point
    return new_info


def get_nodes(info):
    nodes = info['nodes'][1:-1].split('), (')
    nodes[0] = nodes[0][1:]
    nodes[-1] = nodes[-1][:-1]
    return nodes


def download_city_xml(city):
    coordinates = get_city_coordinates(city)
    south = round(coordinates[0], 4)
    north = round(coordinates[1], 4)
    west = round(coordinates[2], 4)
    east = round(coordinates[3], 4)
    url = f"https://overpass-api.de/api/map?bbox={west},{south},{east},{north}"
    response = requests.get(url, stream=True)
    bar = tqdm(desc='Скачано уже', unit='B', unit_scale=True)
    with open(os.path.join('xml', f"{city}.xml"), 'wb') as f:
        for chunk in response.iter_content(chunk_size=10 * 1024 * 1024):
            if chunk:
                bar.update(1024 * 10 * 8)
                f.write(chunk)
        bar.close()


def get_city_coordinates(city):
    connection = sqlite3.connect(os.path.join('db', 'cities.db'))
    connection.create_function('NORMALIZE', 1, normalize_string_sqlite)
    cursor = connection.cursor()
    cursor.execute(f"SELECT south, north, west, east FROM cities "
                   f"WHERE NORMALIZE(name) IN ('{normalize_string_sqlite(city)}')")
    result = cursor.fetchall()
    if len(result) == 0:
        print('Такого города в базе нет.')
        exit(3)
    if len(result) > 1:
        print('Нашлось больше одного города с таким названием. Уточните запрос.')
        exit(4)
    coordinates = result[0]
    connection.close()
    return coordinates


if __name__ == '__main__':
    main()

