import xml.etree.ElementTree
import sqlite3
import os
from tqdm import tqdm
from extensions import get_average_point

class Parser:
    def __init__(self, city: str) -> None:
        self.city = city + '.xml'
        self.connection = sqlite3.connect(os.path.join('db', f'{self.city[:-4]}.db'))
        self.cursor = self.connection.cursor()

        self.rows_count = 0

        self.ways = {}
        self.refs_ways = {}

        self.relations = {}
        self.refs_relations = {}

    def parse(self) -> None:
        self.get_tables()
        tree = xml.etree.ElementTree.iterparse(os.path.join('xml', self.city))
        bar = tqdm(total=self.rows_count, desc='Формирование базы', ncols=100)
        for event, elem in tree:
            bar.update(1)
            if elem.tag == 'node':
                self.parse_node(elem)
                elem.clear()
            elif elem.tag == 'way':
                self.parse_way(elem)
                elem.clear()
            elif elem.tag == 'relation':
                if len(self.ways) > 0:
                    self.insert_ways_to_base()
                self.parse_relation(elem)
                elem.clear()
        if len(self.relations) > 0:
            self.insert_relations_to_base()
        del tree
        self.connection.commit()
        self.connection.close()
        bar.close()

    def get_tables(self) -> None:
        node_tags = set()
        way_tags = set()
        tree = xml.etree.ElementTree.iterparse(os.path.join('xml', self.city))
        self.rows_count = 0
        bar = tqdm(desc='Обработано уже', unit=' строк')
        for event, elem in tree:
            self.rows_count += 1
            if elem.tag == 'node':
                for tag in list(elem):
                    key = tag.attrib['k'].lower()
                    if key not in ['id', 'lat', 'lon']:
                        node_tags.add(key)
                elem.clear()
            elif elem.tag == 'way':
                for child in list(elem):
                    if child.tag == 'tag':
                        key = child.attrib['k'].lower()
                        if key not in ['id', 'nodes']:
                            way_tags.add(key)
                elem.clear()
            elif elem.tag == 'relation':
                is_building = self.is_building(list(elem))
                for child in list(elem):
                    if child.tag == 'tag' and is_building:
                        key = child.attrib['k'].lower()
                        if key not in ['id', 'nodes']:
                            way_tags.add(key)
                elem.clear()
            bar.update(1)
        del tree
        bar.close()
        str_node = ""
        for tag in node_tags:
            str_node += f', [{tag}] TEXT'
        str_way = ""
        for tag in way_tags:
            str_way += f', [{tag}] TEXT'
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS nodes "
                            f"(id INTEGER, lat DOUBLE, lon DOUBLE{str_node})")
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS ways"
                            f"(id INTEGER, nodes TEXT, lat DOUBLE, lon DOUBLE{str_way})")

    def parse_node(self, elem) -> None:
        tags = list(elem)
        attr = elem.attrib
        keys = ['id', 'lat', 'lon']
        values = [attr['id'], attr['lat'], attr['lon']]
        for tag in tags:
            key = tag.attrib['k'].lower()
            value = tag.attrib['v']
            keys.append(key)
            values.append(value)
        self.insert_row('nodes', keys, values)

    def parse_way(self, elem) -> None:
        children = list(elem)
        attr = elem.attrib
        keys = ['id']
        values = [attr['id']]
        nodes_count = 0
        for child in children:
            if child.tag == 'nd':
                ref = child.attrib['ref']
                if ref not in self.refs_ways:
                    self.refs_ways[ref] = set()
                self.refs_ways[ref].add((attr['id'], nodes_count))
                nodes_count += 1
            elif child.tag == 'tag':
                key = child.attrib['k'].lower()
                value = child.attrib['v']
                keys.append(key)
                values.append(value)
        self.ways[attr['id']] = ([0]*nodes_count, keys, values)
        if len(self.ways) > 100000:
            self.insert_ways_to_base()

    def insert_ways_to_base(self) -> None:
        self.cursor.execute(f"SELECT id, lat, lon FROM nodes "
                            f"WHERE id IN "
                            f"{'(' + ', '.join(self.refs_ways.keys()) + ')'}")
        coordinates = self.cursor.fetchall()
        for coord in coordinates:
            ids = self.refs_ways[str(coord[0])]
            for id, index in ids:
                self.ways[id][0][index] = ([coord[1], coord[2]])
        for way in self.ways.values():
            keys = way[1]
            values = way[2]
            aver_point = get_average_point(way[0])
            if aver_point is None:
                continue
            keys = keys[:1] + ['nodes', 'lat', 'lon'] + keys[1:]
            values = values[:1] + [str(way[0]), aver_point[0], aver_point[1]] + values[1:]
            self.insert_row('ways', keys, values)

        self.ways = {}
        self.refs_ways = {}

    def parse_relation(self, elem) -> None:
        children = list(elem)
        attr = elem.attrib
        keys = ['id']
        values = [attr['id']]
        count = 0
        if not self.is_building(children):
            return
        for child in children:
            if child.tag == 'tag':
                key = child.attrib['k'].lower()
                value = child.attrib['v']
                keys.append(key)
                values.append(value)
            elif child.tag == 'member' and child.attrib['role'] != 'inner':
                ref = child.attrib['ref']
                count += 1
                if ref not in self.refs_relations:
                    self.refs_relations[ref] = set()
                self.refs_relations[ref].add((attr['id'], count))

        self.relations[attr['id']] = ([], keys, values)
        #TODO подумать как парсить школы, детские сады и пр.
        #TODO подумать что делать когда одно здание пожирает другое
        #TODO некоторые организации не точки, а линии
        #TODO теги организаций - shop, amenity, и еще чето
        if len(self.relations) > 100000:
            self.insert_relations_to_base()

    def insert_relations_to_base(self):
        self.cursor.execute(f"SELECT id, lat, lon FROM nodes "
                            f"WHERE id IN "
                            f"{'(' + ', '.join(self.refs_relations.keys()) + ')'}")
        nodes = self.cursor.fetchall()

        indexer = []
        for node in nodes:
            ids = self.refs_relations[str(node[0])]
            for id, index in ids:
                indexer.append((node, id, index))

        self.cursor.execute(f"SELECT id, nodes FROM ways "
                            f"WHERE id IN "
                            f"{'(' + ', '.join(self.refs_relations.keys()) + ')'}")
        ways = self.cursor.fetchall()

        for way in ways:
            ids = self.refs_relations[str(way[0])]
            for id, index in ids:
                indexer.append((way, id, index))

        indexer = sorted(indexer, key=lambda x: x[2])
        for obj, id, index in indexer:
            if len(obj) == 3:
                self.relations[id][0].append([obj[1], obj[2]])
            else:
                nodes = obj[1][1:-1].split('], [')
                nodes[0] = nodes[0][1:]
                nodes[-1] = nodes[-1][:-1]
                for node in nodes:
                    node = node.split(', ')
                    self.relations[id][0].append([float(node[0]), float(node[1])])

        for relation in self.relations.values():
            keys = relation[1]
            values = relation[2]

            aver_point = get_average_point(relation[0])

            if aver_point is None:
                continue

            keys = keys[:1] + ['nodes', 'lat', 'lon'] + keys[1:]
            values = values[:1] + [str(relation[0]), aver_point[0], aver_point[1]] + values[1:]

            self.insert_row('ways', keys, values)
        self.relations = {}
        self.refs_relations = {}

    def insert_row(self, table: str, keys: list, values: list) -> None:
        keys = map(lambda x: f'[{x}]', keys)
        keys = '(' + ', '.join(keys) + ')'
        values_to_question_marks = '?' + ', ?' * (len(values) - 1)
        self.cursor.execute(f"INSERT INTO {table} {keys} "
                            f"VALUES ({values_to_question_marks})",
                            tuple(values))

    @staticmethod
    def is_building(elem):
        for child in elem:
            if child.tag == 'tag' and \
                    'addr:street' in child.attrib['k']:
                return True
        return False
