import os
from pathlib import Path
#TODO везде на Path поменять os.path.join
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from mongita import MongitaClientDisk

from config import NODES_COUNT, WAYS_COUNT, RELATIONS_COUNT


class Parser:
    def __init__(self, city: str) -> None:
        path = Path.cwd() / 'db-mongita' / city
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        client = MongitaClientDisk(host=path)
        db = client['db']
        self.ways = db['ways']
        self.nodes = db['nodes']
        self.city_file = city + '.xml'
        self.i = 0
        self.nodes_result = []
        self.ways_result = []
        self.nodes_coordinates = {}
        self.ways_coordinates = {}

    def parse(self) -> None:
        tree = ElementTree.iterparse(
            os.path.join('xml', self.city_file))
        for _, element in tree:
            if element.tag == 'node':
                self.parse_node(element)
                element.clear()
            elif element.tag == 'way':
                if len(self.nodes_result) > 0:
                    self.nodes.insert_many(self.nodes_result)
                    self.nodes_result = []
                self.parse_way(element)
                element.clear()
            if element.tag == 'relation':
                self.parse_relation(element)
                element.clear()
        if len(self.ways_result) > 0:
            self.ways.insert_many(self.ways_result)
            self.ways_result = []
        del tree

    def parse_node(self, elem: Element):
        tags = list(elem)
        attr = elem.attrib
        # TODO float сделать
        result = {'id': attr['id'], 'lat': attr['lat'], 'lon': attr['lon']}
        self.nodes_coordinates[attr['id']] = (attr['lat'], attr['lon'])
        for tag in tags:
            key = tag.attrib['k'].lower()
            value = tag.attrib['v']
            result[key] = value
        self.nodes_result.append(result)
        if len(self.nodes_result) > NODES_COUNT:
            self.nodes.insert_many(self.nodes_result)
            self.nodes_result = []

    def parse_way(self, way: Element) -> None:
        subelements = list(way)
        attributes = way.attrib
        result = {'id': attributes['id']}
        nodes = []
        # TODO стайл поправить во всех методах
        for child in subelements:
            if child.tag == 'nd':
                ref = child.attrib['ref']
                nodes.append(self.nodes_coordinates[ref])
            elif child.tag == 'tag':
                key = child.attrib['k'].lower()
                value = child.attrib['v']
                result[key] = value
        result['nodes'] = tuple(nodes)
        self.ways_result.append(result)
        self.ways_coordinates[attributes['id']] = tuple(nodes)
        if len(self.ways_result) > WAYS_COUNT:
            self.ways.insert_many(self.ways_result)
            self.ways_result = []

    def parse_relation(self, relation: Element) -> None:
        subelements = list(relation)
        attributes = relation.attrib
        result = {'id': attributes['id'], 'nodes': []}
        if not self.is_building(subelements):
            return
        # TODO поправить когда relation тоже мембер
        for child in subelements:
            if child.tag == 'member' \
                    and (child.attrib['role'] in ('outline', 'outer')):
                ref = child.attrib['ref']
                if child.attrib['type'] == 'node':
                    try:
                        result['nodes'].append(self.nodes_coordinates[ref])
                    except KeyError:
                        continue
                elif child.attrib['type'] == 'way':
                    try:
                        result['nodes'] += list(self.ways_coordinates[ref])
                    except KeyError:
                        continue
            elif child.tag == 'tag':
                key = child.attrib['k'].lower()
                value = child.attrib['v']
                result[key] = value
        self.ways_result.append(result)
        if len(self.ways_result) > RELATIONS_COUNT:
            self.ways.insert_many(self.ways_result)
            self.ways_result = []

    @staticmethod
    def is_building(element: Element) -> bool:
        street_flag, housenumber_flag = False, False
        for child in element:
            try:
                if 'addr:street' in child.attrib['k']:
                    street_flag = True
                if 'addr:housenumber' in child.attrib['k']:
                    housenumber_flag = True
                if street_flag and housenumber_flag:
                    return True
            except KeyError:
                continue
        return False


if __name__ == '__main__':
    from time import time

    start = time()
    Parser('Санкт-Петербург').parse()
    print(time() - start)
