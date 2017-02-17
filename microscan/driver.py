import serial


class MS3Driver(object):
    def __init__(self, port):
        self.port = port

    def __enter__(self):
        self.connect()

    def __exit__(self):
        self.close()

    def connect(self):
        # default settings as per page 3-1 of the user manual:
        # 9600 baud, 7 bits, 1 stop bit, no flow control
        self.port = serial.Serial(
            self.port,
            baudrate=9600,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE,
            timeout=None,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )

    def close(self):
        self.port.close()
