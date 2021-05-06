import xml.etree.ElementTree
import sqlite3


class Parser:
    def __init__(self, city):
        self.city = city
        self.connection = sqlite3.connect(f'{self.city}.db')
        self.cursor = self.connection.cursor()
        self.nodes_parameters = set()
        self.ways_parameters = set()
        self.indexer_node = 0
        self.indexer_way = 0
        self.ways = {}
        self.refs = dict()

    def parse(self):
        tree = xml.etree.ElementTree.iterparse(self.city)
        self.get_tables(self.city)
        for event, elem in tree:
            if elem.tag == 'node':
                self.parse_node(elem)
            elif elem.tag == 'way':
                self.parse_way(elem)
            elif elem.tag == 'relation':
                if len(self.ways) > 0:
                    self.insert_ways_to_base()
                self.parse_relation(elem)
        self.connection.commit()
        self.connection.close()

    def get_tables(self, city):
        node_tags = set()
        way_tags = set()
        tree = xml.etree.ElementTree.iterparse(city)
        for event, elem in tree:
            if elem.tag == 'node':
                for tag in list(elem):
                    key = tag.attrib['k'].lower()
                    node_tags.add(key)
            elif elem.tag == 'way':
                for child in list(elem)[::-1]:
                    if child.tag == 'tag':
                        key = child.attrib['k'].lower()
                        way_tags.add(key)
                    else:
                        break
            elif elem.tag == 'relation':
                for child in list(elem)[::-1]:
                    if child.tag == 'tag' \
                            and self.is_building(list(elem)[::-1]):
                        key = child.attrib['k'].lower()
                        way_tags.add(key)
                    else:
                        break

        str_node = ""
        for tag in node_tags:
            str_node += f', [{tag}] TEXT'
        str_way = ""
        for tag in way_tags:
            str_way += f', [{tag}] TEXT'
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS nodes'
                            f'(id INTEGER, lat DOUBLE, lon DOUBLE{str_node})')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS ways'
                            f'(id INTEGER, nodes TEXT{str_way})')

    def parse_node(self, elem):
        tags = list(elem)
        attr = elem.attrib
        keys = ['id', 'lat', 'lon']
        values = [attr['id'], attr['lat'], attr['lon']]

        # print('node', self.indexer_node)
        # self.indexer_node += 1

        for tag in tags:
            key = tag.attrib['k'].lower()
            value = tag.attrib['v'].lower()

            keys.append(key)
            values.append(value)
        self.insert_row('nodes', keys, values)

    def parse_way(self, elem):
        children = list(elem)[::-1]
        attr = elem.attrib
        keys = ['id']
        values = [attr['id']]

        # print('way', self.indexer_way)
        # self.indexer_way += 1

        # if is_highway():
        #   return

        nodes_count = 0
        for child in children:
            if child.tag == 'nd':
                ref = child.attrib['ref']
                if ref not in self.refs:
                    self.refs[ref] = set()
                self.refs[ref].add(attr['id'])
                nodes_count += 1
            elif child.tag == 'tag':
                key = child.attrib['k'].lower()
                value = child.attrib['v'].lower()

                keys.append(key)
                values.append(value)
        self.ways[attr['id']] = (set(), keys, values)

        if len(self.ways) > 3000:
            self.insert_ways_to_base()

    def insert_ways_to_base(self):
        self.cursor.execute(f"SELECT id, lat, lon FROM nodes "
                            f"WHERE id IN "
                            f"{'(' + ', '.join(self.refs.keys()) + ')'}")
        coordinates = self.cursor.fetchall()

        print(len(coordinates))

        for coord in coordinates:
            ids = self.refs[str(coord[0])]

            for id in ids:
                self.ways[id][0].add((coord[1], coord[2]))
                # if coord[0] == 1337298929:
                # print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
                # print(self.refs[str(coord[0])])
                # print(self.ways[id])

        for way in self.ways.values():
            keys = way[1]
            values = way[2]
            keys = keys[:1] + ['nodes'] + keys[2:]
            values = values[:1] + [str(way[0])] + values[2:]
            self.insert_row('ways', keys, values)
        self.ways = {}
        self.refs = dict()

    def parse_relation(self, elem):
        children = list(elem)[::-1]
        keys = ['id']
        values = [elem.attrib['id']]
        if not self.is_building(children):
            return
        print('-------------')
        print(elem.attrib)
        points = set()

        for child in children:
            if child.tag == 'tag':
                key = child.attrib['k'].lower()
                value = child.attrib['v'].lower()
                keys.append(key)
                values.append(value)
            elif child.tag == 'member':
                type = child.attrib['type']
                ref = child.attrib['ref']
                print(ref)
                if type == 'node':
                    self.cursor.execute(f'SELECT lat, lon FROM nodes '
                                        f'WHERE id IN ({ref})')
                    node_coord = self.cursor.fetchone()[0]
                    points.add(str(tuple(node_coord)))
                elif type == 'way':
                    self.cursor.execute(f'SELECT nodes FROM ways '
                                        f'WHERE id IN ({ref})')
                    a = self.cursor.fetchone()
                    print(a)
                    nodes = a[0][1:-1].split('), (')
                    nodes[0] = nodes[0][1:]
                    nodes[-1] = nodes[-1][:-1]

                    for node in nodes:
                        points.add('(' + node + ')')
        keys = keys[:1] + ['nodes'] + keys[2:]
        values = values[:1] + [str(points)] + values[2:]
        self.insert_row('ways', keys, values)

    # def insert_row(self, table, keys, values):
    #     question_marks = '?' + ', ?' * (len(values) - 1)
    #     self.cursor.execute(f"INSERT INTO {table} {question_marks} VALUES ({question_marks})", tuple(keys + values))

    def insert_row(self, table, keys, values):
        keys = map(lambda x: f'[{x}]', keys)
        keys = '(' + ', '.join(keys) + ')'
        values_to_question_marks = '?' + ', ?' * (len(values) - 1)
        self.cursor.execute(f"INSERT INTO {table} {keys} "
                            f"VALUES ({values_to_question_marks})",
                            tuple(values))

    @staticmethod
    def is_building(children):
        for child in children:
            if child.tag == 'tag':
                # if 'highway' in child.attrib['k']:
                #     return False
                if 'addr:street' in child.attrib['k']:
                    return True
        return False


if __name__ == "__main__":
    parser = Parser('Izhevsk')
    parser.parse()
