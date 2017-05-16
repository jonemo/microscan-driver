from copy import deepcopy
import re
import serial
import time
import warnings

from .config import MicroscanConfiguration


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
            self, port, baudrate=None, parity=None, stopbits=None,
            databits=None):
        self.port = port
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
            self.port,
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
            if prev_buffer_size == buffer_size:
                break
            if time.time() - start_of_wait > timeout:
                break
        read_content = self.port.read_all()
        # find each setting string and create config from list of lines
        config_lines = re.findall(b'<K[^>]*>', read_content)
        cfg = MicroscanConfiguration.from_config_strings(config_lines)
        # keep internal copy of device configuration up to date and give
        # requester a copy
        self._config = cfg
        return deepcopy(cfg)

    @property
    def config(self):
        return self._config

    def read_barcode(self):
        self.port.write(b'*')
        buffer_contents = self.port.read_all()
        last_line = buffer_contents.strip().split(b'\r\n')[-1]
        return last_line.decode('ascii', errors='ignore')


class MS2Driver(MicroscanDriver):
    """
    Extends MicroscanDriver with features specific to the MS2 barcode reader
    """


class MS3Driver(MicroscanDriver):
    """
    Extends MicroscanDriver with features specific to the MS3 barcode reader
    """
