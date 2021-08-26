import os

import pytest

import direct_geocoder
import downloader
import organizations
import reverse_geocoder
import utils


class TestDownloader:
    def test_get_city_coordinates(self):
        actual = downloader.get_city_coordinates('Ижевск')
        assert actual == (56.7164064, 57.0047551, 53.006558, 53.3913797)

    def test_get_city_coordinates_when_not_find(self):
        with pytest.raises(SystemExit) as e:
            downloader.get_city_coordinates('Абракадабра')
        assert e.type == SystemExit
        assert e.value.code == 3


class TestDirectGeocoder:
    @staticmethod
    def setup():
        default_setup()

    def test_do_geocoding(self):
        city, street, house_number = 'Первоуральск', 'Юбилейная', '10'
        actual = direct_geocoder.do_geocoding(city, street, house_number)
        expected = {'id': '87346929',
                    'building': 'yes',
                    'addr:country': 'RU',
                    'building:levels': '5',
                    'nodes': [(56.885344, 60.004033),
                              (56.8853313, 60.0042086),
                              (56.8846975, 60.0040549),
                              (56.8847102, 60.0038793),
                              (56.885344, 60.004033)],
                    'coordinates': (56.8850854, 60.0040418),
                    'addr:city': 'Первоуральск',
                    'addr:street': 'Юбилейная улица',
                    'addr:housenumber': '10',
                    'lat': '56.8850854',
                    'lon': '60.0040418'}
        assert actual == expected

    def test_do_geocoding_when_point_not_in_city(self):
        city, street, house_number = 'Первоуральск', \
                                     'Пушкина', \
                                     'Колотушкина'
        with pytest.raises(SystemExit) as e:
            direct_geocoder.do_geocoding(city, street, house_number)
        assert e.type == SystemExit
        assert e.value.code == 1

    def test_do_geocoding_when_more_point_in_city(self):
        city, street, house_number = 'Первоуральск', 'А', '10'
        with pytest.raises(SystemExit) as e:
            direct_geocoder.do_geocoding(city, street, house_number)
        assert e.type == SystemExit
        assert e.value.code == 2

    def test_get_new_info(self):
        info = {'abra': None,
                'nodes': '[[1, 1], [2, 2], [3, 3]]',
                'abc': 'hello world!'}
        actual = direct_geocoder.form_geocoder_answer(info)
        expected = {'nodes': [(1, 1), (2, 2), (3, 3)],
                    'coordinates': (2, 2),
                    'abc': 'hello world!'}
        assert actual == expected


class TestReverseGeocoder:
    @staticmethod
    def setup():
        default_setup()

    def test_find_city(self):
        lat, lon = 56.846675, 53.241569
        actual = reverse_geocoder.find_city(lat, lon)
        assert actual[0] == 'Ижевск' and actual[1] == 'Удмуртия'

    def test_find_city_when_point_not_in_city(self):
        lat, lon = 57.8907, 53.4099
        with pytest.raises(SystemExit) as e:
            reverse_geocoder.find_city(lat, lon)
        assert e.type == SystemExit
        assert e.value.code == 6

    def test_do_reverse_geocoding(self):
        lat, lon, city = 56.8850854, 60.0040418, 'Первоуральск'
        actual = reverse_geocoder.do_reverse_geocoding(lat, lon, city)
        expected = {'id': '87346929',
                    'building': 'yes',
                    'addr:country': 'RU',
                    'building:levels': '5',
                    'nodes': [(56.885344, 60.004033),
                              (56.8853313, 60.0042086),
                              (56.8846975, 60.0040549),
                              (56.8847102, 60.0038793),
                              (56.885344, 60.004033)],
                    'coordinates': (56.8850854, 60.0040418),
                    'addr:city': 'Первоуральск',
                    'addr:street': 'Юбилейная улица',
                    'addr:housenumber': '10',
                    'lat': '56.8850854',
                    'lon': '60.0040418'}
        assert actual == expected

    def test_reverse_when_point_not_in_home_and_not_in_zone(self):
        lat, lon, city = 56.9170, 59.9413, 'Первоуральск'
        with pytest.raises(SystemExit) as e:
            reverse_geocoder.do_reverse_geocoding(lat, lon, city)
        assert e.type == SystemExit
        assert e.value.code == 8

    def test_reverse_when_point_not_in_home_but_many_in_zone(self):
        lat, lon, city = 56.91243, 59.93996, 'Первоуральск'
        with pytest.raises(SystemExit) as e:
            reverse_geocoder.do_reverse_geocoding(lat, lon, city)
        assert e.type == SystemExit
        assert e.value.code == 9

    def test_reverse_when_point_not_in_home_but_after_one_found(self):
        lat, lon, city = 56.90741, 59.93146, 'Первоуральск'
        actual = reverse_geocoder.do_reverse_geocoding(lat, lon, city)
        expected = {'id': '208731781',
                    'building': 'apartments',
                    'addr:country': 'RU',
                    'building:levels': '5',
                    'addr:postcode': '623101',
                    'nodes': [(56.9071298, 59.9311299),
                              (56.9076668, 59.9312141),
                              (56.9076585, 59.9313911),
                              (56.9071215, 59.9313069),
                              (56.9071298, 59.9311299)],
                    'coordinates': (56.9073413, 59.9312344),
                    'addr:city': 'Первоуральск',
                    'addr:street': 'проспект Космонавтов',
                    'addr:housenumber': '5',
                    'lat': '56.9073413',
                    'lon': '59.9312344'}
        assert actual == expected

    def test_cross(self):
        assert reverse_geocoder.cross((1, 1), (2, 2)) == 0

    def test_dot(self):
        assert reverse_geocoder.dot((1, 2), (3, 4)) == 11

    def test_is_point_in_polygon_when_in_polygon(self):
        point = (0.5, 0.5)
        polygon = [(0, 0), (1, 0), (1, 1), (0, 1)]
        actual = reverse_geocoder.is_point_in_polygon(point, polygon)
        expected = True
        assert actual == expected

    def test_is_point_in_polygon_when_not_in_polygon(self):
        point = (2, 2)
        polygon = [(0, 0), (1, 0), (1, 1), (0, 1)]
        actual = reverse_geocoder.is_point_in_polygon(point, polygon)
        expected = False
        assert actual == expected

    def test_is_point_in_polygon_when_empty_polygon(self):
        point = (1, 1)
        polygon = []
        actual = reverse_geocoder.is_point_in_polygon(point, polygon)
        expected = False
        assert actual == expected

    def test_is_point_in_polygon_when_point_on_border(self):
        point = (0.5, 1)
        polygon = [(0, 0), (1, 0), (1, 1), (0, 1)]
        actual = reverse_geocoder.is_point_in_polygon(point, polygon)
        expected = True
        assert actual == expected

    def test_is_point_in_polygon_when_point_is_vertex(self):
        point = (1, 1)
        polygon = [(0, 0), (1, 0), (1, 1), (0, 1)]
        actual = reverse_geocoder.is_point_in_polygon(point, polygon)
        expected = True
        assert actual == expected


class TestOrganizations:
    def setup(self):
        default_setup()

    def test_get_info_with_organizations(self):
        city, street, house_number = 'Первоуральск', \
                                     'проспект Ильича', \
                                     '10'
        info = direct_geocoder.do_geocoding(city, street, house_number)
        actual = organizations.get_organizations_by_address_border(city, info)
        organizations_expected = {'organizations': [{'id': 4679512990,
                                                     'lat': 56.9041403,
                                                     'lon': 59.9490692,
                                                     'amenity': 'bank',
                                                     'name': 'ВУЗ-Банк',
                                                     'name:en': 'VUZBANK',
                                                     'name:ru': 'ВУЗ-Банк'}]}
        expected = {**info, **organizations_expected}
        assert actual == expected

    def test_zip_elements(self):
        columns = ['a', 'b']
        organizations_list = [(None, 'abc'), (5, None), ('yy', 'xx')]
        actual = organizations.zip_table_columns_with_table_rows(columns,
                                                                 organizations_list)
        expected = [{'b': 'abc'}, {'a': 5}, {'a': 'yy', 'b': 'xx'}]
        assert actual == expected

    def test_zip_elements_when_columns_empty(self):
        columns = []
        organizations_list = [(None, 'abc'), (5, None), ('yy', 'xx')]
        actual = organizations.zip_table_columns_with_table_rows(columns,
                                                                 organizations_list)
        expected = [{}, {}, {}]
        assert actual == expected

    def test_zip_elements_when_organizations_empty(self):
        columns = ['a', 'b']
        organizations_list = []
        actual = organizations.zip_table_columns_with_table_rows(columns,
                                                                 organizations_list)
        expected = []
        assert actual == expected


class TestUtils:
    def test_download_city_xml(self):
        if not utils.is_file_exist(f'Первоуральск.xml',
                                   os.path.join('xml')):
            downloader.download_city_xml('Первоуральск')
        assert utils.is_file_exist(f'Первоуральск.xml',
                                   os.path.join('xml'))

    def test_get_fixed_city_name_and_region_with_small_letter(self):
        actual = utils.get_fixed_city_and_region_name('ижевск')
        assert actual[0] == 'Ижевск' and actual[1] == 'Удмуртия'

    def test_get_fixed_city_name_and_region_without_dash(self):
        actual = utils.get_fixed_city_and_region_name('санктпетербург')
        assert actual[0] == 'Санкт-Петербург' and \
               actual[1] == 'Санкт-Петербург'

    def test_get_average_point(self):
        points = [(0, 1), (1, 0), (0, 0), (1, 1)]
        assert utils.get_average_point(points) == (0.5, 0.5)

    def test_get_average_point_when_empty_list(self):
        points = []
        assert utils.get_average_point(points) is None

    def test_normalize_string_sqlite(self):
        s = 'Abra-ca dabrA'
        assert utils.normalize_string_sqlite(s) == 'abracadabra'

    def test_get_nodes(self):
        s = '[[1, 1], [2, 2], [3, 3]]'
        assert utils.get_nodes(s) == ['1, 1', '2, 2', '3, 3']

    def test_get_nodes_when_empty_list(self):
        s = ''
        assert utils.get_nodes(s) == ['']


def default_setup():
    downloader.get_base('Первоуральск')
