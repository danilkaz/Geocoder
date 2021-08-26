import os

import json
from answer import GeocoderAnswer, GeocoderAnswerEncoder


def output_answer_to_json_file(answer: GeocoderAnswer,
                               path: str,
                               reverse=False) -> None:
    region = answer.region.replace(' ', '_')
    city = answer.city.replace(' ', '_')
    street = answer.street.replace(' ', '_')
    house_number = answer.house_number.replace(' ', '_')
    lat, lon = answer.lat, answer.lon
    #TODO lat lon поправить
    file_name = f'{region}_{city}_{street}_{house_number}.json'
    if reverse:
        file_name = f'{lat}_{lon}.json'
    if path == 'json':
        path = os.path.join(path, file_name)
    splitted_path = os.path.split(os.path.abspath(path))
    if not os.path.exists(splitted_path[0]):
        os.makedirs(splitted_path[0])
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(answer, f, ensure_ascii=False, cls=GeocoderAnswerEncoder)
        print(f'\nФайл сохранен по пути: "{path}"')
    except PermissionError:
        print('Ошибка доступа.')
        exit(13)
    except FileNotFoundError:
        print('Ошибка создания файла. '
              'Проверьте корректность пути и имени файла.')
        exit(14)


def print_answer(answer: GeocoderAnswer,
                 additional=False,
                 organizations=False) -> None:
    region = answer.region
    city = answer.city
    street = answer.street
    house_number = answer.house_number
    lat, lon = answer.lat, answer.lon
    print(f'\nАдрес: {region}, {city}, {street}, {house_number}')
    print(f'Координаты: ({lat}, {lon})')
    if additional:
        print('\nДополнительная информация OpenStreetMap:')
        for key, value in answer.additional_information.items():
            print(f'{key} : {value}')
    if organizations:
        print('\nОрганизации в здании:')
        for i, organization in enumerate(answer.organizations):
            if str(organization['id']) == \
                    str(answer.additional_information['id']):
                continue
            print(i + 1)
            for key, value in organization.items():
                print(f"{key} : {value}")
