import xml.etree.ElementTree
import sqlite3


class Parser:
    def __init__(self):
        self.connection = sqlite3.connect('Izh.db')
        self.cursor = self.connection.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS nodes(id INTEGER, lat DOUBLE, lon DOUBLE)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS ways(id INTEGER, nodes TEXT)")
        self.nodes_parameters = set()
        self.ways_parameters = set()
        self.indexer_node = 0
        self.indexer_way = 0

    def parse(self, city):
        tree = xml.etree.ElementTree.iterparse(city)
        for event, elem in tree:
            if elem.tag == 'node':
                self.parse_node(elem)
            elif elem.tag == 'way':
                self.parse_way(elem)
            elif elem.tag == 'relation':
                pass
                #self.parse_relation(elem)
            else:
                continue
        self.connection.commit()
        self.connection.close()

    def parse_node(self, elem):
        tags = list(elem)
        attr = elem.attrib
        keys = ['id', 'lat', 'lon']
        values = [attr['id'], attr['lat'], attr['lon']]
        print("node", self.indexer_node)
        self.indexer_node += 1
        for tag in tags:
            key = self.replace_service_words(tag.attrib['k'])
            value = tag.attrib['v']
            if key not in self.nodes_parameters:
                self.add_column('nodes', key, self.nodes_parameters)
            keys.append(key)
            values.append(value)
        self.insert_row('nodes', keys, values)

    def parse_way(self, elem):
        children = list(elem)[::-1]
        attr = elem.attrib
        keys = ['id']
        values = [attr['id']]
        print('way', self.indexer_way)
        self.indexer_way += 1
        if not self.is_building(children):
            return
        refs = []
        for child in children:
            if child.tag == 'nd':
                ref = child.attrib['ref']
                refs.append(ref)
            elif child.tag == 'tag':
                key = self.replace_service_words(child.attrib['k'])
                value = child.attrib['v']
                if key not in self.ways_parameters:
                    self.add_column('ways', key, self.ways_parameters)
                keys.append(key)
                values.append(value)
        self.cursor.execute(f"SELECT lat, lon FROM nodes WHERE id IN {'('+ ', '.join(refs) + ')'}")
        coordinates = str(self.cursor.fetchall())
        keys = keys[:1] + ['nodes'] + keys[2:]
        coordinates = ' '.join(coordinates)
        values = values[:1] + [coordinates] + values[2:]
        self.insert_row('ways', keys, values)

    def parse_relation(self, elem):
        children = list(elem)[::-1]
        attr = elem.attrib

        keys = ['id']
        values = [attr['id']]

        if not self.is_building(children):
            return

        for child in children:
            if child.tag == 'member':
                type = child.attrib['type']
                ref = child.attrib['ref']
                if type == 'way':
                    pass
                else:
                    pass
            else:
                pass

    def add_column(self, table, key, parameters):
        parameters.add(key)
        self.cursor.execute(f'ALTER TABLE {table} ADD COLUMN {key} TEXT')

    def insert_row(self, table, keys, values):
        keys = '(' + ', '.join(keys) + ')'
        values_to_question_marks = '?' + ', ?' * (len(values) - 1)
        self.cursor.execute(f"INSERT INTO {table} {keys} VALUES ({values_to_question_marks})", tuple(values))

    def select_row(self, table, *args):
        pass

    @staticmethod
    def is_building(children):
        for child in children:
            if child.tag == 'tag':
                if 'highway' in child.attrib['k']:
                    return False
                elif 'addr:street' in child.attrib['k']:
                    return True
        return False

    @staticmethod
    def replace_service_words(string):
        string = string.lower()
        characters = {':': 'COLON', '.': 'DOT', 'index': 'post_index'}
        for character in characters.keys():
            string = string.replace(character, characters[character])
        return string


if '__main__' == __name__:
    parser = Parser()
    parser.parse('Izhevsk')
