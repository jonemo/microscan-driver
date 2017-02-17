from argparse import ArgumentParser
from sys import exit

from microscan.driver import MS3Driver


parser = parser = ArgumentParser(
    description='XMLRPC server interface to Microscan barcode scanner')
parser.add_argument(
    'port', type=str, help='an integer for the accumulator')
args = parser.parse_args()


def main():
    driver = MS3Driver(port=args.port)
    driver.connect()
    try:
        while True:
            print(driver.port.readline())
    except:
        driver.close()
        return 0


if __name__ == '__main__':
    exit(main())
