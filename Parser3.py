import pymongo
import xml.etree.ElementTree


class Parser:
    def __init__(self):
        DEFAULT_CONNECTION_URL = "mongodb://localhost:27017/"
        database_name = "Izh_DB"
        self.client = pymongo.MongoClient(DEFAULT_CONNECTION_URL)

        database = self.client[database_name]

        self.table_nodes = database['nodes']
        self.table_ways = database['ways']


        # self.connection = sqlite3.connect('Izh.db')
        # self.cursor = self.connection.cursor()
        #
        # self.nodes_parameters = set()
        # self.ways_parameters = set()
        # self.indexer_node = 0
        # self.indexer_way = 0

    def parse(self, city):
        tree = xml.etree.ElementTree.iterparse(city)

        for event, elem in tree:
            if elem.tag == 'node':
                self.parse_node(elem)
            # elif elem.tag == 'way':
            #     self.parse_way(elem)
            # elif elem.tag == 'relation':
            #     self.parse_relation(elem)

    def parse_node(self, elem):
        tags = list(elem)
        attr = elem.attrib

        d = {
            'id': attr['id'],
             'lat': attr['lat'],
             'lon': attr['lon']
             }

        for tag in tags:
            key = self.replace_service_words(tag.attrib['k'])
            value = tag.attrib['v']

            d[key] = value

        self.insert_row(self.table_nodes, d)

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

                keys.append(key)
                values.append(value)
        self.cursor.execute(f"SELECT lat, lon FROM nodes WHERE id IN {'('+ ', '.join(refs) + ')'}")
        coordinates = str(self.cursor.fetchmany(len(refs)))
        keys = keys[:1] + ['nodes'] + keys[2:]
        coordinates = ' '.join(coordinates)
        values = values[:1] + [coordinates] + values[2:]
        self.insert_row('ways', keys, values)

    def parse_relation(self, elem):
        pass

    def insert_row(self, table, d):
        table.insert_one(d)

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
