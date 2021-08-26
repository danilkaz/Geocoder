import direct_geocoder
import reverse_geocoder
from answer import GeocoderAnswer
from downloader import get_base
from organizations import get_organizations_by_address_border
from utils import (get_fixed_city_and_region_name,
                   find_city_and_region,
                   check_and_update_city_and_region)

try:
    import requests
    from tqdm import tqdm
except ImportError:
    print('Не установлены необходимые модули')
    print('Выполните команду: pip install -r requirements.txt')
    exit(10)


def direct_geocoding(city: str,
                     street: str,
                     house_number: str,
                     organizations: bool = False) -> GeocoderAnswer:
    city, region = get_fixed_city_and_region_name(city)
    get_base(city)
    answer = direct_geocoder.do_geocoding(city, street, house_number)
    if organizations:
        answer.organizations = \
            get_organizations_by_address_border(
                city, answer.additional_information['nodes'])
    check_and_update_city_and_region(answer, region, city)
    return answer


def reverse_geocoding(lat: str,
                      lon: str,
                      organizations: bool = False) -> GeocoderAnswer:
    lat = float(lat.replace(',', '.'))
    lon = float(lon.replace(',', '.'))
    city, region = find_city_and_region(lat, lon)
    get_base(city)
    answer = reverse_geocoder.do_reverse_geocoding(city, lat, lon)
    if organizations:
        answer.organizations = \
            get_organizations_by_address_border(
                city, answer.additional_information['nodes'])
    check_and_update_city_and_region(answer, region, city)
    return answer
