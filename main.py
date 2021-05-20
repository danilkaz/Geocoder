import argparse
import sqlite3
import os

from downloader import Downloader
from xml_parser import Parser
from reverse_geocoder import ReverseGeocoder
from geocoder import Geocoder
from extensions import normalize_string_sqlite
from printer import print_info, get_json_file, print_organizations
from organizations import get_info_with_organizations

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print('Не установлены необходимые модули')
    print('Выполните команду: pip install -r requirements.txt')
    exit(10)

def main():
    create_directories()

    args = parse_arguments()

    if args.reverse:
        lat = float(args.reverse[0])
        lon = float(args.reverse[1])
        city = find_city(lat, lon)
        get_base(city)
        info = ReverseGeocoder.get_objects(lat, lon, city)
        get_answer(args, city, info)

    elif args.geocoder:
        parsed_city = args.geocoder[0]
        parsed_street = args.geocoder[1]
        parsed_house_number = args.geocoder[2]

        city = fix_city_name(parsed_city)
        get_base(city)

        info = Geocoder.do_geocoding(city, parsed_street, parsed_house_number)
        get_answer(args, city, info)

    else:
        print('Неверный запрос')
        exit(5)

def get_answer(args, city, info):
    if args.organizations:
        info = get_info_with_organizations(city, info)
    if args.json:
        get_json_file(city, info)
    else:
        print_info(city, info, additional=args.additional)
        if args.organizations:
            print_organizations(info)

def fix_city_name(city):
    city_conn = sqlite3.connect(os.path.join('db', 'cities.db'))
    city_conn.create_function('NORMALIZE', 1, normalize_string_sqlite)
    city_cursor = city_conn.cursor()
    city_cursor.execute(f"SELECT name FROM cities "
                        f"WHERE NORMALIZE(name) IN ('{normalize_string_sqlite(city)}')")
    city = city_cursor.fetchall()[0][0]
    # TODO: обработать исключение: город не найден
    # TODO: addr:letter добавить
    city_conn.close()
    return city

def get_base(city):
    if not is_file_exist(f'{city}.db', os.path.join('db')):
        if not is_file_exist(f'{city}.xml', os.path.join('xml')):
            Downloader.download_city_xml(city)
        parser = Parser(city)
        parser.parse()

def find_city(lat, lon):
    connection = sqlite3.connect(os.path.join('db', 'cities.db'))
    cursor = connection.cursor()

    cursor.execute(f"SELECT name FROM cities WHERE ({lat} BETWEEN south AND north) AND ({lon} BETWEEN west AND east)")
    info = cursor.fetchall()
    if len(info) == 0:
        print('Данная точка не находится в городе')
        exit(6)
    elif len(info) > 1:
        print('Точка лежит в пересечении городов')
        exit(7)
        # TODO подумать как исправить
    return info[0][0]

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


def parse_arguments():
    arg_parser = argparse.ArgumentParser('Геокодер')
    # TODO перевести ошибки на русский(если возможно)
    # TODO дополнительный аргумент для ситуаций с совпадениями
    group = arg_parser.add_mutually_exclusive_group()
    group.add_argument('-g', '--geocoder', nargs=3, type=str, required=False,
                       metavar=('city', 'street', 'house_number'), help='Используйте для прямого геокодинга')
    reverse_group = arg_parser.add_mutually_exclusive_group()
    reverse_group.add_argument('-r', '--reverse', nargs=2, type=float, required=False,
                               metavar=('lat', 'lon'), help='Используйте для обратного геокодинга')
    arg_parser.add_argument('-j', '--json', action='store_true', help='Вывод в файл .json')
    arg_parser.add_argument('-a', '--additional', action='store_true',
                           help='Получить дополнительную информации о здании')
    arg_parser.add_argument('-o', '--organizations', action='store_true',
                           help='Дополнительно вывести все организации в здании')
    args = arg_parser.parse_args()
    return args


if __name__ == '__main__':
    main()
