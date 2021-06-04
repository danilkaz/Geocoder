import argparse

import geocoder
from printer import get_json_file, print_info, print_organizations
from extensions import create_directories

def main():
    create_directories()
    arg_parser = argparse.ArgumentParser('Геокодер')
    group = arg_parser.add_mutually_exclusive_group()
    group.add_argument('-g', '--geocoder',
                       nargs=3, type=str,
                       required=False,
                       metavar=('city', 'street', 'house_number'),
                       help='Используйте для прямого геокодинга')
    reverse_group = arg_parser.add_mutually_exclusive_group()
    reverse_group.add_argument('-r', '--reverse',
                               nargs=2, type=str,
                               required=False,
                               metavar=('lat', 'lon'),
                               help='Используйте для обратного геокодинга')

    arg_parser.add_argument('-j', '--json', nargs='?', const='json',
                            metavar='path',
                            help='[опционально] укажите путь до json файла')

    arg_parser.add_argument('-a', '--additional',
                            action='store_true',
                            help='Получить дополнительную '
                                 'информацию о здании')
    arg_parser.add_argument('-o', '--organizations',
                            action='store_true',
                            help='Дополнительно вывести '
                                 'все организации в здании')
    args = arg_parser.parse_args()
    info = {}
    if args.geocoder:
        city, street, house_number = args.geocoder
        info = geocoder.direct_geocoding(city, street, house_number, args.organizations)
    elif args.reverse:
        lat, lon = args.reverse
        info = geocoder.reverse_geocoding(lat, lon, args.organizations)
    else:
        print('Неверный запрос')
        exit(5)
    if args.json:
        get_json_file(info, args.json, reverse=args.reverse)
    else:
        print_info(info, additional=args.additional)
        if args.organizations:
            print_organizations(info)


if __name__ == '__main__':
    main()
