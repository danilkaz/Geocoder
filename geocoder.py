import Parser
import argparse

class Geocoder:
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--address", help="blabla", action="store_true")

    args = parser.parse_args()
    print(args.address)

if __name__ == '__main__':
    main()