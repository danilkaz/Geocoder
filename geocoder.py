import Parser
import argparse
import sqlite3
class Geocoder:
    pass


def main():
    # parser = argparse.ArgumentParser()
    street = 'Холмогорова'
    house_number = '34'

    connection = sqlite3.connect('Izhevsk.db')
    cursor = connection.cursor()
    cursor.execute(f"""SELECT id, nodes FROM ways WHERE ((lower(addrCOLONstreet) LIKE lower('%{street}%')) AND (lower(addrCOLONhousenumber) = lower('{house_number}')))""")
    # print(cursor.fetchall()[0][1])
    nodes = cursor.fetchall()[0][1][1:-1].split('), (')
    nodes[0] = nodes[0][1:]
    nodes[-1]= nodes[-1][:-1]

    pairs = map(lambda p: p.split(', '), nodes)
    x = 0
    y = 0
    n = 0
    # print(n)
    for pair in pairs:
        pair[0], pair[1] = float(pair[0]), float(pair[1])
        print(pair)
        x += pair[0]
        y += pair[1]
        n += 1
    print(round(x / n, 7), round(y / n, 7))
    # parser.add_argument("-a", "--address", help="blabla", action="store_true")

    # args = parser.parse_args()
    # print(args.address)


if __name__ == '__main__':
    main()