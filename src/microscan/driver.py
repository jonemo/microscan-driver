from copy import deepcopy
import re
import serial
import time
import warnings

from .config import MicroscanConfiguration
from .config import TriggerMode


class MicroscanDriver:
    """Base class for Microscan barocode reader drivers

    Serial communication parameters may be passed either to the class
    constructor or when calling the connect() method. See `connect()` for
    details on how connection parameters are determined.

    Device specific drivers might implement additional functionality that is
    not available across the full range of devices.

    Supports use as context manager which ensures the serial connection is
    closed on exiting:
    ```
    with MicroscanDriver('COM1') as driver:
        driver.connect()
        driver.
    ```
    """
    def __init__(
            self, portname, baudrate=None, parity=None, stopbits=None,
            databits=None):
        self.portname = portname
        self.baudrate = baudrate
        self.parity = parity
        self.stopbits = stopbits
        self.databits = databits

        self._config = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    def connect(
            self, baudrate=None, parity=None, databits=None, stopbits=None):
        """Open a serial port for communication with barcode reader device

        Connection settings are taken from three possible locations in the
        following order:

        - method arguments
        - object properties set directly or in constructor or
          detect_connection_settings()
        - default device settings according to device documentation

        If connection settings (baud rate, parity, etc.) are neither provided
        as arguments nor previously set as object properties, for example by
        a search with the detect_connection_settings() method, the default
        values specified in the device documentation are used. For example,
        page 3-1 of the MS3 user manual specifies:
            - baud rate: 9600
            - parity: even
            - data bits: 7
            - stop bits: 1
            - flow control: none
        """
        baudrate = baudrate or self.baudrate or 9600
        parity = parity or self.parity or serial.PARITY_EVEN
        bytesize = databits or self.databits or serial.SEVENBITS
        stopbits = stopbits or self.stopbits or serial.STOPBITS_ONE

        self.port = serial.Serial(
            self.portname,
            baudrate=baudrate,
            parity=parity,
            bytesize=bytesize,
            stopbits=stopbits,
            timeout=1,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )

        self._config = self.read_config()

    def close(self):
        """Close the serial port

        Any subsequent method call that attempts to write to or read from the
        device will result in a serial.SerialException.
        """
        self.port.close()

    def write(self, bytes_):
        """Write arbitrary bytes to the serial port

        Passsing a unicode string instead of bytes will raise a warning and
        the method will attempt to ASCII-encode the string before sending.

        Writing to a closed port, for example before calling connect(), will
        raise a serial.SerialException.
        """
        if isinstance(bytes_, str):
            warnings.warn(
                'write() got unicode string "%s", attempting to convert to '
                'bytes' % bytes_, UnicodeWarning)
            bytes_ = bytes_.encode('ascii')

        self.port.write(bytes_)

    def read_config(self, timeout=2.0):
        """Read device configuration from device by sending the <K?> command

        The `timeout` argument can be used to specify how long the function
        will wait for a complete response from the device. The default value
        (2 seconds) exceeds the typical response time of the device by
        approximately a factor of two.
        """
        # stop scanning to avoid having symbols mixed with configuration data,
        # see page A-10 of documentation
        self.write(b'<I>')
        self.port.flush()

        # Send query for all <K...> codes
        self.write(b'<K?>')
        # Each line contains multiple <K...> settings, no need to read line by
        # line. Instead wait until the buffer stops growing, then read entire
        # response at once.
        buffer_size = 0
        start_of_wait = time.time()
        while True:
            time.sleep(0.1)
            prev_buffer_size = buffer_size
            buffer_size = self.port.in_waiting
            if buffer_size > 0 and prev_buffer_size == buffer_size:
                break
            if time.time() - start_of_wait > timeout:
                break
        read_content = self.port.read_all()

        # resume scanning, see page A-10 of documentation
        self.write(b'<H>')

        # find each setting string and create config from list of lines
        config_lines = re.findall(b'<K[^>]*>', read_content)
        cfg = MicroscanConfiguration.from_config_strings(config_lines)
        # keep internal copy of device configuration up to date and give
        # requester a copy
        self._config = cfg
        return deepcopy(cfg)

    def write_config(self):
        """Write device config to device by sending a series of <K...> commands
        """
        if not isinstance(self._config, MicroscanConfiguration):
            raise TypeError(
                'Expected MicroscanConfiguration but found %s' %
                type(self._config).__name__)

        # stop scanning, see page A-10 of documentation
        self.write(b'<I>')
        # write concatenated config string
        self.write(self._config.to_config_string())
        # resume scanning, see page A-10 of documentation
        self.write(b'<H>')

    @property
    def config(self):
        return self._config

    def read_barcode(self):
        """Reads a single barcode symbol from the device

        If serial trigger is enabled in the current configuration, the
        appropriate trigger is symbol ("Start Trigger Character") or trigger
        message ("Serial Trigger Character") is sent and the next barcode
        returned, with the function blocking until then or the serial read
        timeout.

        If serial trigger is disabled, the most recently read barcode is
        returned if any data is in the serial in buffer, otherwise the method
        will block and wait for the next barcode until the serial read timeout.
        """
        if self._config.trigger.trigger_mode == TriggerMode.SerialData:
            if self._config.start_trigger_character.start_trigger_character:
                as_hex = self._config.start_trigger_character.start_trigger_character  # nopep8
                trigger = bytes([int(as_hex, 16)])
            else:
                trigger = b'<%s>' % self._config.serial_trigger.serial_trigger_character  # nopep8
            # discard any symbols read before trigger is sent
            self.port.flush()
            self.port.write(trigger)
            line = self.port.readline()
        else:
            # when not triggering with a serial command, assume that one or
            # more barcodes are already in the buffer
            buffer_contents = self.port.read_all()
            # TODO: Use postamble setting instead of default '\r\n'
            lines = buffer_contents.split(b'\r\n')
            # the buffer was [bc1][postamble][bc2][postample]..., therefore the
            # last entry in lines should be empty, the second to last is the
            # barcode
            if len(lines) > 2 and lines[-1] == b'':
                line = lines[-2]
            # if there wasn't a line, wait until timeout
            else:
                line = self.port.readline()

        return line.strip().decode('ascii', errors='ignore')


class MS2Driver(MicroscanDriver):
    """
    Extends MicroscanDriver with features specific to the MS2 barcode reader
    """


class MS3Driver(MicroscanDriver):
    """
    Extends MicroscanDriver with features specific to the MS3 barcode reader
    """
