import xml.etree.ElementTree
import sqlite3


class Parser:
    def __init__(self):
        self.connection = sqlite3.connect('Izh.db')
        self.cursor = self.connection.cursor()

        self.nodes_parameters = set()
        self.ways_parameters = set()
        self.indexer_node = 0
        self.indexer_way = 0
        self.ways = []

    def parse(self, city):
        tree = xml.etree.ElementTree.iterparse(city)

        self.get_tables(city)

        for event, elem in tree:
            if elem.tag == 'node':
                self.parse_node(elem)
            elif elem.tag == 'way':
                self.parse_way(elem)
            elif elem.tag == 'relation':
                self.parse_relation(elem)

        self.connection.commit()

    def get_tables(self, city):
        node_tags = set()
        way_tags = set()

        tree = xml.etree.ElementTree.iterparse(city)
        for event, elem in tree:
            if elem.tag == 'node':
                for tag in list(elem):
                    key = self.replace_service_words(tag.attrib['k'])
                    node_tags.add(key)
            elif elem.tag == 'way':
                for child in list(elem)[::-1]:
                    if child.tag == 'tag':
                        key = self.replace_service_words(child.attrib['k'])
                        way_tags.add(key)
                    else:
                        break

        print(node_tags)
        print()
        print(way_tags)

        str_node = ""
        for tag in node_tags:
            str_node += f', {tag} TEXT'

        str_way = ""
        for tag in way_tags:
            str_way += f', {tag} TEXT'

        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS nodes(id INTEGER, lat DOUBLE, lon DOUBLE{str_node})')
        self.cursor.execute(f'CREATE TABLE IF NOT EXISTS ways(id INTEGER, nodes TEXT{str_way})')

    def parse_node(self, elem):
        tags = list(elem)
        attr = elem.attrib
        keys = ['id', 'lat', 'lon']
        values = [attr['id'], attr['lat'], attr['lon']]



        for tag in tags:
            key = self.replace_service_words(tag.attrib['k'])
            value = tag.attrib['v']

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
        nodes_count = 0
        for child in children:
            if child.tag == 'nd':
                ref = child.attrib['ref']
                refs.append(ref)
                nodes_count += 1
            elif child.tag == 'tag':
                key = self.replace_service_words(child.attrib['k'])
                value = child.attrib['v']

                keys.append(key)
                values.append(value)

        self.ways.append((nodes_count, keys, values))

        if len(self.ways) > 3000:
            self.cursor.execute(f"SELECT lat, lon FROM nodes WHERE id IN {'('+ ', '.join(refs) + ')'}")
            coordinates = self.cursor.fetchall()
            i = 0
            for way in self.ways:
                coord = coordinates[i:i+way[0]]
                i += way[0]
                keys = way[1]
                values = way[2]
                keys = keys[:1] + ['nodes'] + keys[2:]
                coord = ' '.join(str(coord))
                values = values[:1] + [coord] + values[2:]
                self.insert_row('ways', keys, values)
            self.ways = []

    def parse_relation(self, elem):
        pass

    def insert_row(self, table, keys, values):
        keys = '(' + ', '.join(keys) + ')'
        values_to_question_marks = '?' + ', ?' * (len(values) - 1)
        self.cursor.execute(f"INSERT INTO {table} {keys} VALUES ({values_to_question_marks})", tuple(values))



    @staticmethod
    def replace_service_words(string):
        string = string.lower()
        characters = {':': 'COLON', '.': 'DOT', 'index': 'post_index'}
        for character in characters.keys():
            string = string.replace(character, characters[character])
        return string

    @staticmethod
    def is_building(children):
        for child in children:
            if child.tag == 'tag':
                if 'highway' in child.attrib['k']:
                    return False
                elif 'addr:street' in child.attrib['k']:
                    return True
        return False


if __name__ == "__main__":
    parser = Parser()
    parser.parse('Izhevsk.xml')
