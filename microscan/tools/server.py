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

# for demo only
import time
from microscan.config import *

changed_configs = [
    UPC_EAN(upc_status=UPCStatus.Enabled),
    Trigger(trigger_mode=TriggerMode.ContinuousReadOneOutput),
    EndReadCycle(
        end_read_cycle_mode=EndReadCycleMode.Timeout,
        read_cycle_timeout=300,
    ),
    DecodesBeforeOutput(
        number_before_output=5,
        decodes_before_output_mode=DecodesBeforeOutputMode.Consecutive,
    ),
    LaserSetup(
        laser_on_off_status=LaserOnOffStatus.Disabled,
    ),
]
# end of for demo only


def main():
    args = parser.parse_args()

    server = SimpleXMLRPCServer(("localhost", args.port))

    try:
        with MS3Driver(args.device) as driver:

            # temporary, for demo only
            for cfg in changed_configs:
                configstr = cfg.to_config_string()
                driver.port.write(configstr)
                time.sleep(0.1)
            # end of for demo only

            server.register_instance(driver, allow_dotted_names=True)
            server.register_introspection_functions()
            server.serve_forever()
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == '__main__':
    exit(main())
