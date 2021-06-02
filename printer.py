import json
import os


def get_json_file(region, city, info, path, reverse=False):
    street = info['addr:street'].replace(' ', '_')
    house_number = info['addr:housenumber'].replace(' ', '_')
    region = region.replace(' ', '_')
    lat, lon = info['coordinates']

    file_name = f'{region}_{city}_{street}_{house_number}.json'
    if reverse:
        file_name = f'{lat}_{lon}.json'
    print(path)
    if path == 'json':
        path = os.path.join(path, file_name)
    splitted_path = os.path.split(os.path.abspath(path))
    if not os.path.exists(splitted_path[0]):
        os.mkdir(splitted_path[0])
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False)
        print(f'\nФайл сохранен по пути: "{path}"')
    except:
        print('Ошибка создания файла. Проверьте корректность пути и имени файла.')
        exit(13)


def print_organizations(info):
    print('\nОрганизации в здании:')
    for i, organization in enumerate(info['organizations']):
        print(i + 1)
        for key, value in organization.items():
            print(f"{key} : {value}")


def print_info(region, city, info, additional=False):
    if 'addr:city' in info:
        city = info['addr:city']
    street = info['addr:street']
    house_number = info['addr:housenumber']
    lat, lon = info['coordinates']
    print()
    print(f'Адрес: {region}, {city}, {street}, {house_number}')
    print(f'Координаты: ({lat}, {lon})')

    if additional:
        print('\nДополнительная информация OpenStreetMap:')
        for key, value in info.items():
            if key not in ['addr:city', 'addr:street', 'addr:housenumber',
                           'coordinates', 'lat', 'lon', 'organizations']:
                print(f'{key} : {value}')
