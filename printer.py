import json
import os

def get_json_file(city, info, reverse=False):
    street = info['addr:street'].replace(' ', '_')
    house_number = info['addr:housenumber'].replace(' ', '_')
    lat, lon = info['coordinates']
    file_name = f'{city}_{street}_{house_number}.json'
    if reverse:
        file_name = f'{lat}_{lon}.json'
    with open(os.path.join('json', file_name), 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False)
    print(f'\nФайл сохранен в папку json с именем "{file_name}"')

def print_organizations(info):
    print('\nОрганизации в здании:')
    for i, organization in enumerate(info['organizations']):
        print(i + 1)
        for key, value in organization.items():
            print(f"{key} : {value}")


def print_info(city, info, additional=False):
    if 'addr:city' in info:
        city = info['addr:city']
    street = info['addr:street']
    house_number = info['addr:housenumber']
    lat, lon = info['coordinates']
    print()
    print(f'Адрес: {city}, {street}, {house_number}')
    print(f'Координаты: ({lat}, {lon})')

    if additional:
        print('\nДополнительная информация OpenStreetMap:')
        for key, value in info.items():
            if key not in ['addr:city', 'addr:street', 'addr:housenumber', 'coordinates', 'lat', 'lon']:
                print(f'{key} : {value}')
