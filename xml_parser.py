import xml.etree.ElementTree
import sqlite3
import os
from tqdm import tqdm


class Parser:
    def __init__(self, city: str) -> None:
        self.city = city + '.xml'
        self.connection = sqlite3.connect(os.path.join('db', f'{self.city[:-4]}.db'))
        self.cursor = self.connection.cursor()
        self.ways = {}
        self.refs_ways = {}
        self.rows_count = 0

        self.relations = {}
        self.refs_rel = {}

    def parse(self) -> None:
        self.get_tables()
        tree = xml.etree.ElementTree.iterparse(os.path.join('xml', self.city))
        bar = tqdm(total=self.rows_count, desc="Формирование базы", ncols=100)
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
        for event, elem in tree:
            self.rows_count += 1
            if elem.tag == 'node':
                for tag in list(elem):
                    key = tag.attrib['k'].lower()
                    if key not in ['id', 'lat', 'lon']:
                        node_tags.add(key)
                elem.clear()
            elif elem.tag == 'way':
                for child in list(elem)[::-1]:
                    if child.tag == 'tag':
                        key = child.attrib['k'].lower()
                        if key not in ['id', 'nodes']:
                            way_tags.add(key)
                    else:
                        break
                elem.clear()
            elif elem.tag == 'relation':
                for child in list(elem)[::-1]:
                    if child.tag == 'tag' \
                            and self.is_building(list(elem)[::-1]):
                        key = child.attrib['k'].lower()
                        if key not in ['id', 'nodes']:
                            way_tags.add(key)
                    else:
                        break
                elem.clear()
        del tree
        str_node = ""
        for tag in node_tags:
            str_node += f', [{tag}] TEXT'
        str_way = ""
        for tag in way_tags:
            str_way += f', [{tag}] TEXT'
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS nodes "
                            f"(id INTEGER, lat DOUBLE, lon DOUBLE{str_node})")
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS ways"
                            f"(id INTEGER, nodes TEXT, coordinateX DOUBLE, coordinateY DOUBLE{str_way})")

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
        children = list(elem)[::-1]
        attr = elem.attrib
        keys = ['id']
        values = [attr['id']]
        nodes_count = 0
        for child in children:
            if child.tag == 'nd':
                ref = child.attrib['ref']
                if ref not in self.refs_ways:
                    self.refs_ways[ref] = set()
                self.refs_ways[ref].add(attr['id'])
                nodes_count += 1
            elif child.tag == 'tag':
                key = child.attrib['k'].lower()
                value = child.attrib['v']
                keys.append(key)
                values.append(value)
        self.ways[attr['id']] = ([], keys, values)
        #TODO не добавлять inner
        if len(self.ways) > 100000:
            self.insert_ways_to_base()

    def insert_ways_to_base(self) -> None:
        self.cursor.execute(f"SELECT id, lat, lon FROM nodes "
                            f"WHERE id IN "
                            f"{'(' + ', '.join(self.refs_ways.keys()) + ')'}")
        coordinates = self.cursor.fetchall()
        for coord in coordinates:
            ids = self.refs_ways[str(coord[0])]
            for id in ids:
                self.ways[id][0].append([coord[1], coord[2]])
        for way in self.ways.values():
            keys = way[1]
            values = way[2]
            aver_point = self.get_average_point(way[0])

            keys = keys[:1] + ['nodes', 'coordinateX', 'coordinateY'] + keys[1:]
            values = values[:1] + [str(way[0]), aver_point[0], aver_point[1]] + values[1:]
            self.insert_row('ways', keys, values)

        self.ways = {}
        self.refs_ways = {}

    def get_average_point(self, points):
        x = 0
        y = 0
        for point in points:
            point[0], point[1] = float(point[0]), float(point[1])
            x += point[0]
            y += point[1]
        return round(x / len(points), 7), round(y / len(points), 7)

    def parse_relation(self, elem) -> None:
        children = list(elem)[::-1]
        #TODO исправить [::-1]
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
            elif child.tag == 'member':
                ref = child.attrib['ref']
                count += 1
                if ref not in self.refs_rel:
                    self.refs_rel[ref] = set()
                self.refs_rel[ref].add(attr['id'])

        self.relations[attr['id']] = ([], keys, values)
        #TODO добавить среднюю точку для relation
        #TODO подумать как парсить школы, детские сады и пр.
        #TODO подумать что делать когда одно здание пожирает другое
        #TODO бинпоиск
        #TODO ашан на боровой проверить углы(геокодер не определяет здание)
        #TODO некоторые организации не точки, а линии
        #TODO теги организаций - shop, amenity, и еще чето
        #TODO парсить nodes сразу много
        if len(self.relations) > 100000:
            self.insert_relations_to_base()

    def insert_relations_to_base(self):
        self.cursor.execute(f"SELECT id, lat, lon FROM nodes "
                            f"WHERE id IN "
                            f"{'(' + ', '.join(self.refs_rel.keys()) + ')'}")
        nodes = self.cursor.fetchall()
        for node in nodes:
            ids = self.refs_rel[str(node[0])]
            for id in ids:
                self.relations[id][0].append( (node[1], node[2]) )
        self.cursor.execute(f"SELECT id, nodes FROM ways "
                            f"WHERE id IN "
                            f"{'(' + ', '.join(self.refs_rel.keys()) + ')'}")
        ways = self.cursor.fetchall()
        for way in ways:
            ids = self.refs_rel[str(way[0])]
            for id in ids:
                nodes = way[1][1:-1].split('], [')
                nodes[0] = nodes[0][1:]
                nodes[-1] = nodes[-1][:-1]
                for node in nodes:
                    node = node.split(', ')
                    self.relations[id][0].append((float(node[0]), float(node[1])))

        for relation in self.relations.values():
            keys = relation[1]
            values = relation[2]
            keys = keys[:1] + ['nodes'] + keys[1:]
            values = values[:1] + [str(relation[0])] + values[1:]
            self.insert_row('ways', keys, values)
        self.relations = {}
        self.refs_rel = {}

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
