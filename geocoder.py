import reverse_geocoder
import direct_geocoder
from extensions import get_fixed_city_and_region_name
from organizations import add_organizations_to_info
from downloader import get_base

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print('Не установлены необходимые модули')
    print('Выполните команду: pip install -r requirements.txt')
    exit(10)


def direct_geocoding(city, street, house_number, organizations=False):
    city, region = get_fixed_city_and_region_name(city)
    get_base(city)
    info = direct_geocoder.do_geocoding(city, street, house_number)
    if 'addr:region' not in info:
        info['addr:region'] = region
    if 'addr:city' not in info:
        info['addr:city'] = city
    if organizations:
        info = add_organizations_to_info(city, info)
    return info


def reverse_geocoding(lat, lon, organizations=False):
    lat = float(lat.replace(',', '.'))
    lon = float(lon.replace(',', '.'))
    city, region = reverse_geocoder.find_city(lat, lon)
    get_base(city)
    info = reverse_geocoder.do_reverse_geocoding(lat, lon, city)
    if 'addr:region' not in info:
        info['region'] = region
    if 'addr:city' not in info:
        info['addr:city'] = city
    if organizations:
        info = add_organizations_to_info(city, info)
    return info

