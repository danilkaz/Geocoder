from xml_parser import Parser
import argparse
import sqlite3
import json
import os
import requests


def main():
    if not is_directory_exist('xml', os.path.curdir):
        os.mkdir('xml')
    if not is_directory_exist('json', os.path.curdir):
        os.mkdir('json')

    argparser = argparse.ArgumentParser('Simple Geocoding')

    argparser.add_argument('-r', '--reverse', action='store_true', help="use reverse geocoding")
    argparser.add_argument('city', type=str, help='Enter city')
    argparser.add_argument('street', type=str, help='Enter street name')
    argparser.add_argument('house_number', type=str, help='Enter house number')
    argparser.add_argument('-j', '--json', action='store_true', help="output into .json file")

    args = argparser.parse_args()

    if not is_file_exist(f'{args.city}.db', os.path.join('db')):
        if not is_file_exist(f'{args.city}.xml', os.path.join('xml')):
            download_city_xml(args.city)
        parser = Parser(args.city)
        parser.parse()

    conn = sqlite3.connect(os.path.join('db', f'{args.city}.db'))
    cursor = conn.cursor()

    if args.reverse:
        pass
    else:
        info = do_geocoding(cursor, args.street, args.house_number)

        if args.json:
            file_name = f'{args.city}_{args.street}_{args.house_number}.json'
            with open(os.path.join('json', file_name), 'w', encoding='utf-8') as fp:
                json.dump(info, fp, ensure_ascii=False)
            print(f'Файл сохранен в папку json с именем "{file_name}"')
        else:
            for key, value in info.items():
                print(f'{key} : {value}')


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
                   f"WHERE ([addr:street] LIKE '%{street.lower()}%') "
                   f"AND ([addr:housenumber] = '{house_number.lower()}')")
    #TODO: добавить нормальное сравнение номера дома
    info = cursor.fetchall()
    if len(info) == 0:
        print('Данный адрес не найден. Проверьте правильность ввода.')
        exit(1)
    if len(info) > 1:
        print('Найдено больше одного адреса. Уточните запрос.')
        exit(2)
    info = info[0]

    new_info = dict()

    nodes = get_nodes(info)
    points = list(map(lambda p: p.split(', '), nodes))
    average_point = get_average_point(points)

    cursor.execute(f"PRAGMA table_info('ways')")
    columns = list(map(lambda t: t[1], cursor.fetchall()))
    for tup in zip(columns, info):
        if tup[1] is not None and tup[0] != 'nodes':
            new_info[str(tup[0])] = str(tup[1])
    new_info['coordinates'] = average_point
    new_info['nodes'] = list(map(tuple, points))

    return new_info


def get_nodes(info):
    nodes = info[1][1:-1].split('), (')
    nodes[0] = nodes[0][1:]
    nodes[-1] = nodes[-1][:-1]
    return nodes


def download_city_xml(city):
    coordinates = get_city_coordinates(city)
    south = round(coordinates[0], 4)
    north = round(coordinates[1], 4)
    west = round(coordinates[2], 4)
    east = round(coordinates[3], 4)
    print(south, north, west, east)
    url = f"https://overpass-api.de/api/map?bbox={west},{south},{east},{north}"
    response = requests.get(url, stream=True)
    with open(os.path.join('xml', f"{city}.xml"), 'wb') as f:
        for chunk in response.iter_content(chunk_size=10 * 1024 * 1024):
            if chunk:
                f.write(chunk)


def get_city_coordinates(city):
    connection = sqlite3.connect(os.path.join('db', 'cities.db'))
    cursor = connection.cursor()
    cursor.execute(f"SELECT south, north, west, east FROM cities WHERE name IN ('{city}')")
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

