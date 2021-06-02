import argparse

def parse_arguments():
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
                            metavar=('path'),
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
    return args