from argparse import ArgumentParser
from sys import exit
from xmlrpc.server import SimpleXMLRPCServer

from microscan.driver import MS3Driver


parser = parser = ArgumentParser(
    description='XMLRPC server interface to Microscan barcode reader')
parser.add_argument(
    'port', type=int, help='Port number for XMLRPC server')
parser.add_argument(
    'device', type=str,
    help='Serial port device name where reader is connected')


def main():
    args = parser.parse_args()

    server = SimpleXMLRPCServer(("localhost", args.port))

    try:
        with MS3Driver(args.device) as driver:
            server.register_instance(driver, allow_dotted_names=True)
            server.register_introspection_functions()
            server.serve_forever()
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == '__main__':
    exit(main())
