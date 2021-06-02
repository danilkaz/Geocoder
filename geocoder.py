import reverse_geocoder
import direct_geocoder
from extensions import create_directories, get_fixed_city_and_region_name
from printer import print_info, get_json_file, print_organizations
from organizations import get_info_with_organizations
from downloader import get_base
from args_parser import parse_arguments

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print('Не установлены необходимые модули')
    print('Выполните команду: pip install -r requirements.txt')
    exit(10)


def geocoding():
    create_directories()
    args = parse_arguments()
    if args.reverse:
        lat = float(args.reverse[0].replace(',', '.'))
        lon = float(args.reverse[1].replace(',', '.'))
        city, region = reverse_geocoder.find_city(lat, lon)
        get_base(city)
        info = reverse_geocoder.do_reverse_geocoding(lat, lon, city)
        get_answer(args, region, city, info, reverse=True)

    elif args.geocoder:
        parsed_city = args.geocoder[0]
        parsed_street = args.geocoder[1]
        parsed_house_number = args.geocoder[2]
        city, region = get_fixed_city_and_region_name(parsed_city)
        get_base(city)
        info = direct_geocoder.do_geocoding(city,
                                            parsed_street,
                                            parsed_house_number)
        get_answer(args, region, city, info)

    else:
        print('Неверный запрос')
        exit(5)


def get_answer(args, region, city, info, reverse=False):
    if args.organizations:
        info = get_info_with_organizations(city, info)
    if args.json:
        get_json_file(region, city, info, args.json, reverse)
    else:
        print_info(region, city, info, additional=args.additional)
        if args.organizations:
            print_organizations(info)
