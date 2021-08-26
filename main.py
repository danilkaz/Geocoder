import argparse

import geocoder
from answer import GeocoderAnswer
from output import output_answer_to_json_file, print_answer
from utils import create_directories


def main() -> None:
    create_directories()
    arg_parser = argparse.ArgumentParser()
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
    answer = GeocoderAnswer()
    if args.geocoder:
        city, street, house_number = args.geocoder
        answer = geocoder.direct_geocoding(city,
                                           street,
                                           house_number,
                                           organizations=args.organizations)
    elif args.reverse:
        lat, lon = args.reverse
        answer = geocoder.reverse_geocoding(lat,
                                            lon,
                                            organizations=args.organizations)
    else:
        print('Неверный запрос')
        exit(5)
    if args.json:
        output_answer_to_json_file(answer, args.json, reverse=args.reverse)
    else:
        print_answer(answer,
                     additional=args.additional,
                     organizations=args.organizations)


if __name__ == '__main__':
    main()
