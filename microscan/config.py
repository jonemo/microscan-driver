from enum import Enum
import logging
import re


logger = logging.getLogger(__name__)


"""
Since the ASCII characters below 32 have special meaning, they need to be
escaped when transmitted as part of a setting. The following string can be used
in regex patterns in place of `.` to match any ASCII character as well as any
escaped ASCII character. The full list of ASCII characters and how they are
escaped is on page A-11 of the MS3 user manual.
"""
ASCII_CHAR = b'.|\^[A-Z\[\\\]\^_]'


class MicroscanConfigException(Exception):
    """Parent class for all configuration related exceptions
    """


class InvalidConfigString(MicroscanConfigException):
    """Raised when decoding or encoding a character string with invalid format

    For example, the following strings would raise this exception when passed
    to HostPortConnection.from_config_string():

    - '<K100,4,0>' because K100 has four parameters, not two
    - '<K100,4,9,1,0>' because the second parameter of K100 is one of [0, 1, 2]
    """


class UnknownConfigString(MicroscanConfigException):
    """Raised when a config string is received for which no serializer is known

    For example, the following strings would raise this exception when passed
    to MicroscanConfiguration.from_config_strings():

    - '<K92,1>' because '92' is not a known configuration ID
    - '<K
    """


class KSetting:
    """Base class for all configuration settings"""
    def to_config_string(self, values):
        # class must have non-empty K_CODE attribute
        assert hasattr(self, 'K_CODE')
        assert isinstance(self.K_CODE, bytes)
        assert len(self.K_CODE) > 0

        # object must be valid
        # TODO: write validators for all settings
        # assert self.is_valid()

        # values must be list
        assert isinstance(values, list)

        def normalize_value(val):
            if isinstance(val, bytes):
                return val
            elif val is None:
                return b''
            else:
                return str(val).encode('ascii')

        # normalize values to bytes, None gets cast to empty string
        values = [normalize_value(val) for val in values]
        str_ = b'<%s,%s>' % (self.K_CODE, b','.join(values))

        # test the generated K-string against the pattern used for decoding
        if not re.match(self.K_PATTERN, str_):
            raise InvalidConfigString(
                'Encoding the %s object resulted in an invalid K-string: "%s"'
                % (self.__class__.__name__, str_.decode('ascii'))
            )

        return str_


# === Host Port Connection setting and corresponding enums ===


class Parity(Enum):
    """Used in HostPortConnection setting"""
    NONE = b'0'
    EVEN = b'1'
    ODD = b'2'


class StopBits(Enum):
    ONE = b'0'
    TWO = b'1'


class DataBits(Enum):
    SEVEN = b'0'
    EIGHT = b'1'


BAUD_RATES = {
    b'0': 600,
    b'1': 1200,
    b'2': 2400,
    b'3': 4800,
    b'4': 9600,
    b'5': 19200,
    b'6': 38400,
    b'7': 57600,
    b'8': 115200,
}


def _serialize_baud_rate(baud_rate):
    baud_rate_to_config_val = dict(
        zip(BAUD_RATES.values(), BAUD_RATES.keys()))
    try:
        return baud_rate_to_config_val[baud_rate]
    except IndexError:
        raise ValueError(
            '%s is not a valid baud rate, must be one of %s' %
            (baud_rate, ', '.join(BAUD_RATES.values())))


def _deserialize_baud_rate(configval):
    try:
        return BAUD_RATES[configval]
    except IndexError:
        raise ValueError(
            '%s is not a valid config value for baud rate, must be one of '
            '%s' % (configval, ', '.join(BAUD_RATES.keys())))


class HostPortConnection(KSetting):
    """See page 3-4 of Microscan MS3 manual for reference

    Note that this section is referred to with the plural "Host Port
    Connections" in the manual, but this library uses the singular, for
    consistency with other settings names.
    """
    K_CODE = b'K100'
    K_PATTERN = b'^<%s,([0-8]),([0-2]),([0-1]),([0-1])>$' % K_CODE

    def __init__(
            self, baud_rate=9600, parity=Parity.NONE, stop_bits=StopBits.ONE,
            data_bits=DataBits.SEVEN):
        self.baud_rate = baud_rate
        self.parity = parity
        self.stop_bits = stop_bits
        self.data_bits = data_bits

    def to_config_string(self):
        return super().to_config_string([
            _serialize_baud_rate(self.baud_rate),
            self.parity.value,
            self.stop_bits.value,
            self.data_bits.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create HostPortConnection object from string returned by the device

        The str_ argument should be the device response to the <K100?>
            command, for example '<K100,4,0,0,0>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            baud_rate, parity, stop_bits, data_bits = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            baud_rate=_deserialize_baud_rate(baud_rate),
            parity=Parity(parity),
            stop_bits=StopBits(stop_bits),
            data_bits=DataBits(data_bits),
        )


# === Host Protocol setting and corresponding enums ===


class Protocol(Enum):
    PointToPoint = b'0'
    PointToPointWithRTSCTS = b'1'
    PointToPointWithXONXOFF = b'2'
    PointToPointWithRTSCTSAndXONXOFF = b'3'
    PollingModeD = b'4'
    Multidrop = b'5'
    UserDefined = b'6'
    UserDefinedMultidrop = b'7'


class HostProtocol(KSetting):
    """See page 3-5 of Microscan MS3 manual for reference

    The protocol options `Multidrop`, `UserDefined`, and `UserDefinedMultidrop`
    require additional settings besides the protocol parameter, which are
    currently not supported by this libary. Refer to pages 3-7 to 3-9 in the
    MS3 user manual for detailed explanations of these Host Protocol settings.
    """
    K_CODE = b'K140'
    K_PATTERN = b'^<%s,([0-7])(,.*)?>$' % K_CODE

    def __init__(self, protocol=Protocol.PointToPoint):
        self.protocol = protocol
        # TODO: protocol 5-7 require additional parameters

    def to_config_string(self):
        return super().to_config_string([
            self.protocol.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create HostProtocol object from string returned by the device

        The str_ argument should be the device response to the <K140?>
            command, for example '<K140,0>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            protocol, _ = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(protocol=Protocol(protocol))


# === Host RS-232/422 Status setting and corresponding enums ===


class RS422Status(Enum):
    Disabled = b'0'
    Enabled = b'1'


class HostRS422Status(KSetting):
    """See page 3-10 of Microscan MS3 manual for reference

    This setting contains a single binary flag for switching between RS-232
    and RS-422 mode.

    When using computer with serial port or USB-to-serial adapter, ensure that
    your hardware supports RS-422 communication before switching the barcode
    reader into RS-422 mode.

    When the Host Protocol is set to `Multidrop` or `UserDefinedMultidrop`
    (both not currently supported by this library), RS-485 is implied and this
    setting is ignored.

    Note that this section is referred to as "Host RS-232/422 Status" in the
    manual.
    """
    K_CODE = b'K102'
    K_PATTERN = b'^<%s,([0-1])?>$' % K_CODE

    def __init__(self, status=RS422Status.Disabled):
        self.status = status

    def to_config_string(self):
        return super().to_config_string([
            self.status.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create HostRS422Status object from string returned by the device

        The str_ argument should be the device response to the <K102?>
            command, for example '<K102,1>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            status, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(status=RS422Status(status))


# === Host RS-232 Auxiliary Port setting and corresponding enums ===


class AuxiliaryPortMode(Enum):
    Disabled = b'0'
    Transparent = b'1'
    HalfDuplex = b'2'
    FullDuplex = b'3'
    DaisyChain = b'4'
    CommandProcessing = b'5'


class DaisyChainIdStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class RS232AuxiliaryPort(KSetting):
    """See page 3-11 of Microscan MS3 manual for reference
    """
    K_CODE = b'K101'
    K_PATTERN = (
        b'<%s,([0-5]),([0-8]),([0-2]),([0-1]),([0-1]),([0-1]),(.{1,2})?>'
        % K_CODE
    )

    def __init__(
            self, aux_port_mode=AuxiliaryPortMode.Disabled, baud_rate=9600,
            parity=Parity.NONE, stop_bits=StopBits.ONE,
            data_bits=DataBits.SEVEN,
            daisy_chain_id_status=DaisyChainIdStatus.Disabled,
            daisy_chain_id='1/'
            ):
        self.aux_port_mode = aux_port_mode
        self.baud_rate = baud_rate
        self.parity = parity
        self.stop_bits = stop_bits
        self.data_bits = data_bits
        self.daisy_chain_id_status = daisy_chain_id_status
        self.daisy_chain_id = daisy_chain_id

    def to_config_string(self):
        return super().to_config_string([
            self.aux_port_mode.value,
            _serialize_baud_rate(self.baud_rate),
            self.parity.value,
            self.stop_bits.value,
            self.data_bits.value,
            self.daisy_chain_id_status.value,
            self.daisy_chain_id,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create RS232AuxiliaryPort object from string returned by the device

        The str_ argument should be the device response to the <K101?>
            command, for example '<K101,2,3,1,1,0,1,AB>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            (
                aux_port_mode, baud_rate, parity, stop_bits, data_bits,
                daisy_chain_id_status, daisy_chain_id
            ) = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            aux_port_mode=AuxiliaryPortMode(aux_port_mode),
            baud_rate=_deserialize_baud_rate(baud_rate),
            parity=Parity(parity),
            stop_bits=StopBits(stop_bits),
            data_bits=DataBits(data_bits),
            daisy_chain_id_status=DaisyChainIdStatus(daisy_chain_id_status),
            daisy_chain_id=daisy_chain_id,
        )


# === Preamble setting and corresponding enums ===


class PreambleStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class Preamble(KSetting):
    """See page 3-20 of Microscan MS3 manual for reference
    """
    K_CODE = b'K141'
    K_PATTERN = b'^<%s,([0-1])?,(.{1,4})?>$' % K_CODE

    def __init__(self, status=PreambleStatus.Disabled, characters=None):
        self.status = status
        self.characters = characters

    def to_config_string(self):
        return super().to_config_string([
            self.status.value,
            self.characters,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create Preamble object from string returned by the device

        The str_ argument should be the device response to the <K141?>
            command, for example '<K141,1,ABCD>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            status, characters = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            status=PreambleStatus(status),
            characters=characters,
        )


# === Postamble setting and corresponding enums ===


class PostambleStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class Postamble(KSetting):
    """See page 3-20 of Microscan MS3 manual for reference
    """
    K_CODE = b'K142'
    K_PATTERN = b'^<%s,([0-1])?,(.{1,4})?>$' % K_CODE

    def __init__(self, status=PostambleStatus.Disabled, characters=None):
        self.status = status
        self.characters = characters

    def to_config_string(self):
        return super().to_config_string([
            self.status.value,
            self.characters,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create Postamble object from string returned by the device

        The str_ argument should be the device response to the <K142?>
            command, for example '<K142,1,A16z>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            status, characters = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            status=PostambleStatus(status),
            characters=characters,
        )


# === LRC Status setting and corresponding enums ===


class LRCStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class LRC(KSetting):
    """See page 3-22 of Microscan MS3 manual for reference

    LRC stands for "Longitudinal Redundancy Check".

    Note that this setting is referred to as "LRC Status" in the user manual
    but called `LRC` here to avoid the name colission with the `LRCStatus`
    enum.
    """
    K_CODE = b'K145'
    K_PATTERN = b'^<%s,([0-1])?>$' % K_CODE

    def __init__(self, status=LRCStatus.Disabled):
        self.status = status

    def is_valid(self):
        return all([
            isinstance(self.status, LRCStatus),
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.status.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create LRC object from string returned by the device

        The str_ argument should be the device response to the <K145?>
            command, for example '<K145,1>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            status, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            status=LRCStatus(status),
        )


# === Inter Character Delay setting and corresponding enums ===


class InterCharacterDelay(KSetting):
    """See page 3-22 of Microscan MS3 manual for reference
    """
    K_CODE = b'K144'
    K_PATTERN = b'^<%s,([\d]{1,3})?>$' % K_CODE

    def __init__(self, delay=0):
        self.delay = delay

    def is_valid(self):
        return all([
            isinstance(self.delay, int),
            self.delay >= 0,
            self.delay <= 255,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.delay,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create InterCharacterDelay object from string returned by the device

        The str_ argument should be the device response to the <K144?>
            command, for example '<K144,123>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            delay, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            delay=int(delay),
        )


# === Multisymbol setting and corresponding enums ===


class Multisymbol(KSetting):
    """See page 4-3 of Microscan MS3 manual for reference
    """
    K_CODE = b'K222'
    K_PATTERN = b'^<%s,([1-5])?,(.)?>$' % K_CODE

    def __init__(self, number_of_symbols=1, multisymbol_separator=','):
        self.number_of_symbols = number_of_symbols
        self.multisymbol_separator = multisymbol_separator

    def is_valid(self):
        return all([
            isinstance(self.number_of_symbols, int),
            self.number_of_symbols >= 0,
            self.number_of_symbols <= 5,
            isinstance(self.multisymbol_separator, str),
            len(self.multisymbol_separator) <= 1,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.number_of_symbols,
            self.multisymbol_separator,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create Multisymbol object from string returned by the device

        The str_ argument should be the device response to the <K144?>
            command, for example '<K222,2,|>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            number_of_symbols, multisymbol_separator = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            number_of_symbols=int(number_of_symbols),
            multisymbol_separator=multisymbol_separator,
        )


# === Trigger setting and corresponding enums ===


class TriggerMode(Enum):
    ContinuousRead = b'0'
    ContinuousReadOneOutput = b'1'
    ExternalLevel = b'2'
    ExternalEdge = b'3'
    SerialData = b'4'
    SerialDataAndExternalEdge = b'5'


class Trigger(KSetting):
    """See page 4-6 of Microscan MS3 manual for reference
    """
    K_CODE = b'K200'
    K_PATTERN = b'^<%s,([0-5])?,([\d]*)?>$' % K_CODE

    def __init__(
            self, trigger_mode=TriggerMode.ContinuousRead,
            trigger_filter_duration=244):
        self.trigger_mode = trigger_mode
        self.trigger_filter_duration = trigger_filter_duration

    def is_valid(self):
        return all([
            isinstance(self.trigger_mode, TriggerMode),
            isinstance(self.trigger_filter_duration, int)
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.trigger_mode.value,
            self.trigger_filter_duration,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create Trigger object from string returned by the device

        The str_ argument should be the device response to the <K200?>
            command, for example '<K200,1,244>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            trigger_mode, trigger_filter_duration = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            trigger_mode=TriggerMode(trigger_mode),
            trigger_filter_duration=int(trigger_filter_duration),
        )


# === External Trigger State setting and corresponding enums ===


class ExternalTriggerState(Enum):
    Negative = b'0'
    Positive = b'1'


class ExternalTrigger(KSetting):
    """See page 4-11 of Microscan MS3 manual for reference

    Note that this setting is referred to as "External Trigger Status" in the
    user manual but called `ExternalTrigger` here to avoid the name colission
    with the `ExternalTriggerState` enum.
    """
    K_CODE = b'K202'
    K_PATTERN = b'^<%s,([0-1])?>$' % K_CODE

    def __init__(self, external_trigger_state=ExternalTriggerState.Positive):
        self.external_trigger_state = external_trigger_state

    def is_valid(self):
        return all([
            isinstance(self.external_trigger_state, ExternalTriggerState),
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.external_trigger_state.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create ExternalTriggerState object from str returned by the device

        The str_ argument should be the device response to the <K202?>
            command, for example '<K202,1>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            external_trigger_state, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            external_trigger_state=ExternalTriggerState(
                external_trigger_state),
        )


# === Serial Trigger setting and corresponding enums ===


class SerialTrigger(KSetting):
    """See page 4-12 of Microscan MS3 manual for reference
    """
    K_CODE = b'K201'
    K_PATTERN = b'^<%s,(.|\^\])?>$' % K_CODE

    def __init__(self, serial_trigger_character='^'):
        self.serial_trigger_character = serial_trigger_character

    def is_valid(self):
        return all([
            isinstance(self.serial_trigger_character, bytes),
            len(self.serial_trigger_character) == 1,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.serial_trigger_character,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create SerialTrigger object from string returned by the device

        The str_ argument should be the device response to the <K201?>
            command, for example '<K201,^>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            serial_trigger_character, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            serial_trigger_character=serial_trigger_character,
        )


# === Non-delimited Start and Stop Characters setting ===


class StartTriggerCharacter(KSetting):
    """See page 4-13 of Microscan MS3 manual for reference

    The user manual groups the `StartTriggerSetting` and `StopTriggerSetting`
    under a single heading "Non-delimited Start and Stop Characters". This
    library treats them as separate settings because they have distinct
    K-codes, K229 and K230.

    Note that the character is encoded as two hex digits and not as the actual
    character, as for example SerialTrigger (K201).
    """
    K_CODE = b'K229'
    K_PATTERN = b'^<%s,([0-9a-fA-F]{2})?>$' % K_CODE

    def __init__(self, start_trigger_character=None):
        self.start_trigger_character = start_trigger_character

    def is_valid(self):
        return all([
            isinstance(self.start_trigger_character, str),
            len(self.start_trigger_character) == 1,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.start_trigger_character,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create StartTriggerCharacter object from str returned by the device

        The str_ argument should be the device response to the <K229?>
            command, for example '<K229,>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            start_trigger_character, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            start_trigger_character=start_trigger_character,
        )


class StopTriggerCharacter(KSetting):
    """See page 4-13 of Microscan MS3 manual for reference

    The user manual groups the `StartTriggerSetting` and `StopTriggerSetting`
    under a single heading "Non-delimited Start and Stop Characters". This
    library treats them as separate settings because they have distinct
    K-codes, K229 and K230.

    Note that the character is encoded as two hex digits and not as the actual
    character, as for example SerialTrigger (K201).
    """
    K_CODE = b'K230'
    K_PATTERN = b'^<%s,([0-9a-fA-F]{2})?>$' % K_CODE

    def __init__(self, stop_trigger_character=None):
        self.stop_trigger_character = stop_trigger_character

    def is_valid(self):
        return all([
            isinstance(self.stop_trigger_character, str),
            len(self.stop_trigger_character) == 1,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.stop_trigger_character,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create StopTriggerCharacter object from str returned by the device

        The str_ argument should be the device response to the <K230?>
            command, for example '<K230,>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            stop_trigger_character, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            stop_trigger_character=stop_trigger_character,
        )


# === End Read Cycle setting and corresponding enums ===


class EndReadCycleMode(Enum):
    Timeout = b'0'
    NewTrigger = b'1'
    TimeoutAndNewTrigger = b'2'


class EndReadCycle(KSetting):
    """See page 4-14 of Microscan MS3 manual for reference

    ready_cycle_timeout is measured in tens of milliseconds, e.g. 100 = 1sec
    """
    K_CODE = b'K220'
    K_PATTERN = b'^<%s,([0-2])?,([\d]*)?>$' % K_CODE

    def __init__(
            self, end_read_cycle_mode=EndReadCycleMode.Timeout,
            read_cycle_timeout=100):
        self.end_read_cycle_mode = end_read_cycle_mode
        self.ready_cycle_timeout = read_cycle_timeout

    def is_valid(self):
        return all([
            isinstance(self.end_read_cycle_mode, EndReadCycleMode),
            isinstance(self.ready_cycle_timeout, int),
            self.ready_cycle_timeout >= 0,
            self.ready_cycle_timeout <= 65535,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.end_read_cycle_mode.value,
            self.ready_cycle_timeout,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create EndReadCycle object from str returned by the device

        The str_ argument should be the device response to the <K220?>
            command, for example '<K220,1,100>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            end_read_cycle_mode, read_cycle_timeout = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            end_read_cycle_mode=EndReadCycleMode(end_read_cycle_mode),
            read_cycle_timeout=int(read_cycle_timeout)
        )


# === Decodes Before Output setting and corresponding enums ===


class DecodesBeforeOutputMode(Enum):
    NonConsecutive = b'0'
    Consecutive = b'1'


class DecodesBeforeOutput(KSetting):
    """See page 4-16 of Microscan MS3 manual for reference
    """
    K_CODE = b'K221'
    K_PATTERN = b'^<%s,([\d]{1,3})?,([0-1])?>$' % K_CODE

    def __init__(
            self, number_before_output=1,
            decodes_before_output_mode=DecodesBeforeOutputMode.NonConsecutive):
        self.number_before_output = number_before_output
        self.decodes_before_output_mode = decodes_before_output_mode

    def is_valid(self):
        return all([
            isinstance(self.number_before_output, int),
            self.number_before_output >= 1,
            self.number_before_output <= 255,
            isinstance(
                self.decodes_before_output_mode, DecodesBeforeOutputMode),
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.number_before_output,
            self.decodes_before_output_mode.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create DecodesBeforeOutput object from string returned by the device

        The str_ argument should be the device response to the <K221?>
            command, for example '<K221,10,1>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            number_before_output, decodes_before_output_mode = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            number_before_output=int(number_before_output),
            decodes_before_output_mode=DecodesBeforeOutputMode(
                decodes_before_output_mode)
        )


# === Scan Speed setting and corresponding enums ===


class ScanSpeed(KSetting):
    """See page 4-17 of Microscan MS3 manual for reference

    Note that the user manual groups the "Scan Speed" setting under the
    "Scanner Setup" heading. This library treats it as separate setting because
    it is stored with a distinct K-code `K500` while all other Scanner Setup
    settings are stored with a K-code of `K504`.
    """
    K_CODE = b'K500'
    K_PATTERN = b'^<%s,([\d]{2,3})?>$' % K_CODE

    def __init__(self, scan_speed=350):
        self.scan_speed = scan_speed

    def is_valid(self):
        return all([
            isinstance(self.scan_speed, int),
            self.scan_speed >= 30,
            self.scan_speed <= 100,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.scan_speed,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create ScanSpeed object from str returned by the device

        The str_ argument should be the device response to the <K500?>
            command, for example '<K500,350>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            scan_speed, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            scan_speed=int(scan_speed),
        )


# === Scanner Setup setting and corresponding enums ===

class AGCSamplingMode(Enum):
    Disabled = b'0'
    LeadingEdge = b'1'
    Continuous = b'2'


class ScannerSetup(KSetting):
    """See page 4-17 of Microscan MS3 manual for reference

    Note that the user manual groups the "Scan Speed" setting under the
    "Scanner Setup" heading. This library treats it as separate setting because
    it is stored with a distinct K-code `K500` while all other Scanner Setup
    settings are stored with a K-code of `K504`.
    """
    K_CODE = b'K504'
    K_PATTERN = (
        b'^<%s,([\d]{2,3})?,([0-2])?,([\d]{2,3})?,([\d]{2,3})?>$' % K_CODE)

    def __init__(
            self, gain_level=350,
            agc_sampling_mode=AGCSamplingMode.Continuous, agc_min=70,
            agc_max=245):
        self.gain_level = gain_level
        self.agc_sampling_mode = agc_sampling_mode
        self.agc_min = agc_min
        self.agc_max = agc_max

    def is_valid(self):
        return all([
            isinstance(self.gain_level, int),
            self.scan_speed >= 40,
            self.scan_speed <= 255,
            isinstance(self.agc_sampling_mode, AGCSamplingMode),
            isinstance(self.agc_min, int),
            self.agc_min >= 40,
            self.agc_min <= 250,
            isinstance(self.agc_max, int),
            self.agc_max >= 60,
            self.agc_max <= 255,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.gain_level,
            self.agc_sampling_mode.value,
            self.agc_min,
            self.agc_max,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create ScannerSetup object from str returned by the device

        The str_ argument should be the device response to the <K504?>
            command, for example '<K504,50,2,60,230>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            gain_level, agc_samling_mode, agc_min, agc_max = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            gain_level=int(gain_level),
            agc_sampling_mode=AGCSamplingMode(agc_samling_mode),
            agc_min=int(agc_min),
            agc_max=int(agc_max),
        )


# === Symbol Detect Status setting and corresponding enums ===


class SymbolDetectStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class SymbolDetect(KSetting):
    """See page 4-19 of Microscan MS3 manual for reference

    Note that the user manual groups the "Symbol Detect Status" setting under
    the "Scanner Setup" heading. This library treats it as separate setting
    because it is stored with a distinct K-code `K505` while all other Scanner
    Setup settings are stored with a K-code of `K504`.
    """
    K_CODE = b'K505'
    K_PATTERN = b'^<%s,([0-1])?,([\d]{1,3})?>$' % K_CODE

    def __init__(
            self, status=SymbolDetectStatus.Disabled, transition_counter=14):
        self.status = status
        self.transition_counter = transition_counter

    def is_valid(self):
        return all([
            isinstance(self.status, SymbolDetectStatus),
            isinstance(self.transition_counter, int),
            self.transition_counter >= 0,
            self.transition_counter <= 255,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.status.value,
            self.transition_counter,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create SymbolDetect object from string returned by the device

        The str_ argument should be the device response to the <K505?>
            command, for example '<K505,1>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            status, transition_counter = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            status=SymbolDetectStatus(status),
            transition_counter=int(transition_counter)
        )


# === Inter Character Delay setting and corresponding enums ===


class MaximumElement(KSetting):
    """See page 4-20 of Microscan MS3 manual for reference
    """
    K_CODE = b'K502'
    K_PATTERN = b'^<%s,([\d]{1,5})?>$' % K_CODE

    def __init__(self, maximum_element=0):
        self.maximum_element = maximum_element

    def is_valid(self):
        return all([
            isinstance(self.maximum_element, int),
            self.maximum_element >= 0,
            self.maximum_element <= 65535,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.maximum_element,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create MaximumElement object from string returned by the device

        The str_ argument should be the device response to the <K502?>
            command, for example '<K502,123>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            maximum_element, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            maximum_element=int(maximum_element),
        )


# === Scan Width Enhance setting and corresponding enums ===


class ScanWidthEnhanceStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class ScanWidthEnhance(KSetting):
    """See page 4-20 of Microscan MS3 manual for reference

    Note that the user manual groups the "Symbol Detect Status" setting under
    the "Scanner Setup" heading. This library treats it as separate setting
    because it is stored with a distinct K-code `K511` while all other Scanner
    Setup settings are stored with a K-code of `K504`.
    """
    K_CODE = b'K511'
    K_PATTERN = b'^<%s,([0-1])?>$' % K_CODE

    def __init__(
            self, status=ScanWidthEnhanceStatus.Disabled):
        self.status = status

    def is_valid(self):
        return all([
            isinstance(self.status, ScanWidthEnhance),
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.status.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create ScanWidthEnhance object from string returned by the device

        The str_ argument should be the device response to the <K511?>
            command, for example '<K511,1>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            status, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            status=ScanWidthEnhanceStatus(status),
        )


# === Laser Setup setting and corresponding enums ===


class LaserOnOffStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class LaserFramingStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class LaserPower(Enum):
    Low = b'0'
    Medium = b'1'
    High = b'2'


class LaserSetup(KSetting):
    """See page 4-20 of Microscan MS3 manual for reference

    Note that the "Laser Power" subsetting of the Laser Setup is mentioned
    twice in the MS3 user manual, once under "Laser Setup" and once under
    "Scanner Setup".
    """
    K_CODE = b'K700'
    K_PATTERN = (
        b'^<%s,([0-1])?,([0-1])?,([\d]{2})?,([\d]{2})?,([0-2])?>$' % K_CODE)

    def __init__(
            self, laser_on_off_status=LaserOnOffStatus.Enabled,
            laser_framing_status=LaserFramingStatus.Enabled,
            laser_on_position=10,
            laser_off_position=95,
            laser_power=LaserPower.High):
        self.laser_on_off_status = laser_on_off_status
        self.laser_framing_status = laser_framing_status
        self.laser_on_position = laser_on_position
        self.laser_off_position = laser_off_position
        self.laser_power = laser_power

    def is_valid(self):
        return all([
            isinstance(self.laser_on_off_status, LaserOnOffStatus),
            isinstance(self.laser_framing_status, LaserFramingStatus),
            isinstance(self.laser_on_position, int),
            self.laser_on_position >= 10,
            self.laser_on_position <= 80,
            isinstance(self.laser_off_position, int),
            self.laser_off_position >= 20,
            self.laser_off_position <= 95,
            isinstance(self.laser_power, LaserPower)
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.laser_on_off_status.value,
            self.laser_framing_status.value,
            self.laser_on_position,
            self.laser_off_position,
            self.laser_power.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create LaserSetup object from string returned by the device

        The str_ argument should be the device response to the <K700?>
            command, for example '<K700,1,1,10,95,1>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            (
                on_off_status, framing_status, on_position, off_position, power
             ) = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            laser_on_off_status=LaserOnOffStatus(on_off_status),
            laser_framing_status=LaserFramingStatus(framing_status),
            laser_on_position=int(on_position),
            laser_off_position=int(off_position),
            laser_power=LaserPower(power)
        )


# === Code 39 setting and corresponding enums ===


class Code39Status(Enum):
    Disabled = b'0'
    Enabled = b'1'


class CheckDigitStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class CheckDigitOutputStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class LargeInterCharacterStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class FixedSymbolLengthStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class FullASCIISetStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class Code39(KSetting):
    """See page 5-3 of Microscan MS3 manual for reference
    """
    K_CODE = b'K470'
    K_PATTERN = (
        b'^<%s,([0-1])?,([0-1])?,([0-1])?,([0-1])?,([0-1])?,([\d]{1,2})?,'
        b'([0-1])?>$' % K_CODE)

    def __init__(
            self,
            status=Code39Status.Enabled,
            check_digit_status=CheckDigitStatus.Disabled,
            check_digit_output=CheckDigitOutputStatus.Disabled,
            large_intercharacter_gap=LargeInterCharacterStatus.Disabled,
            fixed_symbol_length=FixedSymbolLengthStatus.Disabled,
            symbol_length=10,
            full_ascii_set=FullASCIISetStatus.Disabled):
        self.status = status
        self.check_digit_status = check_digit_status
        self.check_digit_output = check_digit_output
        self.large_intercharacter_gap = large_intercharacter_gap
        self.fixed_symbol_length = fixed_symbol_length
        self.symbol_length = symbol_length
        self.full_ascii_set = full_ascii_set

    def is_valid(self):
        return all([
            isinstance(self.status, Code39Status),
            isinstance(self.check_digit_status, CheckDigitStatus),
            isinstance(self.check_digit_output, CheckDigitOutputStatus),
            isinstance(
                self.large_intercharacter_gap, LargeInterCharacterStatus),
            isinstance(self.fixed_symbol_length, FixedSymbolLengthStatus),
            isinstance(self.symbol_length, int),
            self.symbol_length >= 1,
            self.symbol_length <= 64,
            isinstance(self.full_ascii_set, FullASCIISetStatus),
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.status.value,
            self.check_digit_status.value,
            self.check_digit_output.value,
            self.large_intercharacter_gap.value,
            self.fixed_symbol_length.value,
            self.symbol_length,
            self.full_ascii_set.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create Code39 object from string returned by the device

        The str_ argument should be the device response to0the <K473?>
            command, for example '<K473,1,0,0,1,1,32,0>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            (
                status, check_digit_status, check_digit_output,
                large_intercharacter_gap, fixed_symbol_length, symbol_length,
                full_ascii_set
             ) = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            status=Code39Status(status),
            check_digit_status=CheckDigitStatus(check_digit_status),
            check_digit_output=CheckDigitOutputStatus(check_digit_output),
            large_intercharacter_gap=LargeInterCharacterStatus(
                large_intercharacter_gap),
            fixed_symbol_length=FixedSymbolLengthStatus(fixed_symbol_length),
            symbol_length=int(symbol_length),
            full_ascii_set=FullASCIISetStatus(full_ascii_set),
        )


# === Code 128 setting and corresponding enums ===


class Code128Status(Enum):
    """Enables/disables the Code 128 symbologies

    See page 5-6 of the Microscan MS3 manual for reference
    """
    Disabled = b'0'
    Enabled = b'1'


class EAN128Status(Enum):
    """Enables/disables/requires the EAN-128 subset of the Code 128 symbology

    EAN-128 is commonly used in shipping applications, defining a wide variaty
    of application specific extensions while using a subset of the possible
    symbols of the Code 128 symbology.

    See page 5-7 of the Microscan MS3 manual for reference
    """
    Disabled = b'0'
    Enabled = b'1'
    Required = b'2'


class Code128OutputFormat(Enum):
    """When EAN-128 is enabled, this setting controls the format of the output

    This setting only takes effect when EAN128Status is set to Enabled or
    Required.

    When this setting is set to ApplicationRecord, the following settings may
    be used for further configuration of the output format:
    - ApplicationRecordSeparatorStatus
    - ApplicationRecordSeparatorCharacter
    - ApplicationRecordBrackets
    - ApplicationRecordPadding

    See page 5-7 of the Microscan MS3 manual for reference
    """
    Standard = b'0'
    ApplicationRecord = b'1'


class ApplicationRecordSeparatorStatus(Enum):
    """Used in conjunction with the Code128OutputFormat setting

    See page 5-8 of the Microscan MS3 manual for reference
    """
    Disabled = b'0'
    Enabled = b'1'


class ApplicationRecordBrackets(Enum):
    """Used in conjunction with the Code128OutputFormat setting

    See page 5-8 of the Microscan MS3 manual for reference
    """
    Disabled = b'0'
    Enabled = b'1'


class ApplicationRecordPadding(Enum):
    """Used in conjunction with the Code128OutputFormat setting

    See page 5-8 of the Microscan MS3 manual for reference
    """
    Disabled = b'0'
    Enabled = b'1'


class Code128(KSetting):
    """See page 5-6 of Microscan MS3 manual for reference

    Code128 is a family of high density symbologies that can encode
    all ASCII characters. The three variants (Code 128-A to C) differ
    in the table of characters, trading off character set with
    density. 128-B allows for all 127 ASCII characters while, while
    128-C is numeric only but encodes two digits in the same space as
    128-B needs for one character.

    Wikipedia: https://en.wikipedia.org/wiki/Code_128

    Properties available in this configuration setting:
     - status (enable/disable Code 128)
     - fixed_symbol_length_status
     - symbol_length
     - ean128_status
     - output_format
     - application_record_separator_status
     - application_record_separator_character
     - application_record_brackets
     - application_record_padding
    """
    K_CODE = b'K474'
    K_PATTERN = (
        b'^<%s,([0-1])?,([0-1])?,([\d]{1,2})?,([0-2])?,([0-1])?,([0-1])?,'
        b'(%s)?,([0-1])?,([0-1])?>$' % (K_CODE, ASCII_CHAR))

    def __init__(
            self,
            status=Code128Status.Disabled,
            fixed_symbol_length_status=FixedSymbolLengthStatus.Disabled,
            symbol_length=10,
            ean128_status=EAN128Status.Disabled,
            output_format=Code128OutputFormat.Standard,
            application_record_separator_status=(
                ApplicationRecordSeparatorStatus.Disabled),
            application_record_separator_character=b',',
            application_record_brackets=ApplicationRecordBrackets.Disabled,
            application_record_padding=ApplicationRecordPadding.Disabled):
        self.status = status
        self.fixed_symbol_length_status = fixed_symbol_length_status
        self.symbol_length = symbol_length
        self.ean128_status = ean128_status
        self.output_format = output_format
        self.application_record_separator_status = (
            application_record_separator_status)
        self.application_record_separator_character = (
            application_record_separator_character)
        self.application_record_brackets = application_record_brackets
        self.application_record_padding = application_record_padding

    def is_valid(self):
        return all([
            isinstance(self.status, Code128Status),
            isinstance(
                self.fixed_symbol_length_status, FixedSymbolLengthStatus),
            isinstance(self.symbol_length, int),
            self.symbol_length >= 1,
            self.symbol_length <= 64,
            isinstance(self.ean128_status, EAN128Status),
            isinstance(self.output_format, Code128OutputFormat),
            isinstance(
                self.application_record_brackets, ApplicationRecordBrackets),
            isinstance(
                self.application_record_padding, ApplicationRecordPadding),
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.status.value,
            self.fixed_symbol_length_status.value,
            self.symbol_length,
            self.ean128_status.value,
            self.output_format.value,
            self.application_record_separator_status.value,
            self.application_record_separator_character,
            self.application_record_brackets.value,
            self.application_record_padding.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create Code128 object from string returned by the device

        The str_ argument should be the device response to0the <K474?>
            command, for example '<K474,1,0,10,1,0,0,,,0,0>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            (
                status,
                fixed_symbol_length_status,
                symbol_length,
                ean128_status,
                output_format,
                application_record_separator_status,
                application_record_separator_character,
                application_record_brackets,
                application_record_padding
            ) = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            status=Code128Status(status),
            fixed_symbol_length_status=FixedSymbolLengthStatus(
                fixed_symbol_length_status),
            symbol_length=int(symbol_length),
            ean128_status=EAN128Status(ean128_status),
            output_format=Code128OutputFormat(output_format),
            application_record_separator_status=(
                ApplicationRecordSeparatorStatus(
                    application_record_separator_status)),
            application_record_separator_character=(
                application_record_separator_character),
            application_record_brackets=ApplicationRecordBrackets(
                application_record_brackets),
            application_record_padding=ApplicationRecordPadding(
                application_record_padding)
        )


# === Interleaved 2 of 5 setting and corresponding enums ===


class Interleaved2Of5Status(Enum):
    Disabled = b'0'
    Enabled = b'1'


class Interleaved2Of5(KSetting):
    """See page 5-10 of Microscan MS3 manual for reference
    """
    K_CODE = b'K472'

    # TODO


# === Codabar setting and corresponding enums ===


class CodabarStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class Codabar(KSetting):
    """See page 5-13 of Microscan MS3 manual for reference
    """
    K_CODE = b'K471'

    # TODO


# === EAN/UPC setting and corresponding enums ===


class UPCStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class EANStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class SupplementalsStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'
    Required = b'2'


class SeparatorStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class UPC_EoutputAsUPC_A(Enum):
    Disabled = b'0'
    Enabled = b'1'


class UPC_EAN(KSetting):
    """See page 5-16 of Microscan MS3 manual for reference
    """
    K_CODE = b'K473'
    # K-codes for this setting can be tricky to read because the last five
    # characters before the closing ">" are likely to be commas:
    # - the second to last sub-setting is unused, i.e. empty
    # - the last and third to last sub-settings default to ","
    K_PATTERN = (
        b'^<%s,([0-1])?,([0-1])?,([0-2])?,([0-1])?,(.)?,,([0-1])?,([0-1])?>$'
        % K_CODE)

    def __init__(
            self,
            upc_status=UPCStatus.Disabled,
            ean_status=EANStatus.Disabled,
            supplementals_status=SupplementalsStatus.Disabled,
            separator_status=SeparatorStatus.Disabled,
            separator_character=',',
            upc_e_output_to_upc_a=UPC_EoutputAsUPC_A.Disabled,  # docs wrong
            undocumented_field=0):
        self.upc_status = upc_status
        self.ean_status = ean_status
        self.supplementals_status = supplementals_status
        self.separator_status = separator_status
        self.separator_character = separator_character
        self.upc_e_output_to_upc_a = upc_e_output_to_upc_a
        self.undocumented_field = undocumented_field

    def is_valid(self):
        return all([
            isinstance(self.upc_status, UPCStatus),
            isinstance(self.ean_status, EANStatus),
            isinstance(self.supplementals_status, SupplementalsStatus),
            isinstance(self.separator_status, SeparatorStatus),
            isinstance(self.separator_character, str),
            isinstance(self.upc_e_output_to_upc_a, UPC_EoutputAsUPC_A),
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.upc_status.value,
            self.ean_status.value,
            self.supplementals_status.value,
            self.separator_status.value,
            self.separator_character,
            None,  # accomodates for the "unused" sub-setting
            self.upc_e_output_to_upc_a.value,
            self.undocumented_field,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create UPC_EAN object from string returned by the device

        The str_ argument should be the device response to the <K473?>
            command, for example '<K473,1,0,0,0,,,,>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            (
                upc_status, ean_status, supplementals_status, separator_status,
                separator_character, upc_e_output_to_upc_a, undocumented_field
             ) = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            upc_status=UPCStatus(upc_status),
            ean_status=EANStatus(ean_status),
            supplementals_status=SupplementalsStatus(supplementals_status),
            separator_status=SeparatorStatus(separator_status),
            separator_character=separator_character,
            upc_e_output_to_upc_a=UPC_EoutputAsUPC_A(upc_e_output_to_upc_a),
            undocumented_field=int(undocumented_field),
        )


# === Code 93 setting and corresponding enums ===


class Code93Status(Enum):
    Disabled = b'0'
    Enabled = b'1'


class Code93(KSetting):
    """See page 5-19 of Microscan MS3 manual for reference
    """
    K_CODE = b'K475'
    K_PATTERN = (
        b'^<%s,([0-1])?,([0-1])?,([\d]{1,2})?>$' % K_CODE)

    def __init__(
            self,
            status=Code93Status.Disabled,
            fixed_symbol_length_status=FixedSymbolLengthStatus.Disabled,
            fixed_symbol_length=10,):
        self.status = status
        self.fixed_symbol_length_status = fixed_symbol_length_status
        self.fixed_symbol_length = fixed_symbol_length

    def is_valid(self):
        return all([
            isinstance(self.status, Code93Status),
            isinstance(
                self.fixed_symbol_length_status, FixedSymbolLengthStatus),
            isinstance(self.fixed_symbol_length, int),
            self.fixed_symbol_length >= 1,
            self.fixed_symbol_length <= 64,
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.status.value,
            self.fixed_symbol_length_status.value,
            self.fixed_symbol_length,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create Code93 object from string returned by the device

        The str_ argument should be the device response to the <K475?>
            command, for example '<K475,1,0,10>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            status, fsl_status, fsl = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            status=Code93Status(status),
            fixed_symbol_length_status=FixedSymbolLengthStatus(fsl_status),
            fixed_symbol_length=int(fsl),
        )


# === Pharmacode setting and corresponding enums ===


class PharmacodeStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class Pharmacode(KSetting):
    """See page 5-19 of Microscan MS3 manual for reference
    """
    K_CODE = b'K475'

    # TODO


# === Narrow Margins and Symbology ID setting and corresponding enums ===


class NarrowMarginsStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class SymbologyIDStatus(Enum):
    Disabled = b'0'
    Enabled = b'1'


class NarrowMarginsAndSymbologyID(KSetting):
    """See page 5-22 of Microscan MS3 manual for reference
    """
    K_CODE = b'K450'
    K_PATTERN = b'^<%s,([0-1])?,([0-1])?>$' % K_CODE

    def __init__(
            self,
            narrow_margins_status=NarrowMarginsStatus.Disabled,
            symbology_id_status=SymbologyIDStatus.Disabled):
        self.narrow_margins_status = narrow_margins_status
        self.symbology_id_status = symbology_id_status

    def is_valid(self):
        return all([
            isinstance(self.narrow_margins_status, NarrowMarginsStatus),
            isinstance(self.symbology_id_status, SymbologyIDStatus)
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.narrow_margins_status.value,
            self.symbology_id_status.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create NarrowMargins object from string returned by the device

        The str_ argument should be the device response to the <K450?>
            command, for example '<K450,1,0>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            narrow_margins_status, symbology_id_status = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            narrow_margins_status=NarrowMarginsStatus(narrow_margins_status),
            symbology_id_status=SymbologyIDStatus(symbology_id_status)
        )


# === Background Color setting and corresponding enums ===


class Color(Enum):
    White = b'0'
    Black = b'1'


class BackgroundColor(KSetting):
    """See page 5-24 of Microscan MS3 manual for reference
    """
    K_CODE = b'K451'
    K_PATTERN = b'^<%s,([0-1])?>$' % K_CODE

    def __init__(self, color=Color.White):
        self.color = color

    def is_valid(self):
        return all([
            isinstance(self.color, Color),
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.color.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create BackgroundColor object from string returned by the device

        The str_ argument should be the device response to the <K451?>
            command, for example '<K451,1>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            color, = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            color=Color(color),
        )


# === Symbol Ratio Mode setting and corresponding enums ===


class SymbolRatio(Enum):
    Tight = b'0'
    Standard = b'1'
    Aggressive = b'2'


class SymbolRatioMode(KSetting):
    """See page 5-25 of Microscan MS3 manual for reference
    """
    K_CODE = b'K452'
    K_PATTERN = b'^<%s,([0-2])?,([0-2])?,([0-2])?,([0-2])?>$' % K_CODE

    def __init__(
            self,
            code39=SymbolRatio.Standard,
            codabar=SymbolRatio.Standard,
            interleaved_2_of_5=SymbolRatio.Standard,
            code93=SymbolRatio.Standard):
        self.code39 = code39
        self.codabar = codabar
        self.interleaved_2_of_5 = interleaved_2_of_5
        self.code93 = code93

    def is_valid(self):
        return all([
            isinstance(self.code39, SymbolRatio),
            isinstance(self.codabar, SymbolRatio),
            isinstance(self.interleaved_2_of_5, SymbolRatio),
            isinstance(self.code93, SymbolRatio),
        ])

    def to_config_string(self):
        return super().to_config_string([
            self.code39.value,
            self.codabar.value,
            self.interleaved_2_of_5.value,
            self.code93.value,
        ])

    @classmethod
    def from_config_string(cls, str_):
        """Create SymbolRatioMode object from string returned by the device

        The str_ argument should be the device response to the <K452?>
            command, for example '<K452,1,1,1,2>'
        """
        match = re.match(cls.K_PATTERN, str_)
        try:
            code39, codabar, il2of5, code93 = match.groups()
        except (ValueError, AttributeError):
            raise InvalidConfigString(
                'Cannot decode config string %s for K-code %s' %
                (str_, cls.K_CODE))

        return cls(
            code39=SymbolRatio(code39),
            codabar=SymbolRatio(codabar),
            interleaved_2_of_5=SymbolRatio(il2of5),
            code93=SymbolRatio(code93),
        )


"""A mapping of K-code to property name and serializer class

For example, maps the K-code 'K100' to the HostPortConnection class which can
be used to serialize or deserialize the device's host port serial protocol
settings (baud rate, parity, ...)
"""
REGISTRY = {cls.K_CODE: cls for cls in [
    HostPortConnection,
    HostProtocol,
    HostRS422Status,
    RS232AuxiliaryPort,
    Preamble,
    Postamble,
    LRC,
    InterCharacterDelay,
    Multisymbol,
    Trigger,
    ExternalTrigger,
    SerialTrigger,
    StartTriggerCharacter,
    StopTriggerCharacter,
    EndReadCycle,
    DecodesBeforeOutput,
    ScanSpeed,
    ScannerSetup,
    SymbolDetect,
    MaximumElement,
    ScanWidthEnhance,
    LaserSetup,
    Code39,
    Code128,
    # Interleaved2Of5,
    # Codabar,
    UPC_EAN,
    Code93,
    # Pharmacode,
    NarrowMarginsAndSymbologyID,
    BackgroundColor,
    SymbolRatioMode,
]}


class MicroscanConfiguration:
    """Container for configuration settings for a barcode reader device

    Calling the constructor will initialize a configuration object with all
    available configuration settings, each set to the default value as
    specified by the device documentation.

    Use MicroscanConfiguration.from_config_strings() to create a configuration
    object from data recorded from a device in response to the `<K?>` command
    (or any other source of configuration data in string format).
    """

    _K_CODE_PATTERN = re.compile(b'<(K\d+)(.*)>')

    def __init__(self):
        self.load_defaults()

    def load_defaults(self):
        """Loads documented default settings into the configuration object

        If called after otherwise setting configuration settings, these will be
        overwritten with defaults by this method.
        """
        for k_code, serializer in REGISTRY.items():
            prop_name = self._clsname_to_propname(serializer.__name__)
            setattr(self, prop_name, serializer())

    @classmethod
    def from_config_strings(cls, list_of_strings, defaults=False):
        """Create configuration object from a list of configuration strings

        Expects a list of byte strings, each representing a configuration
        setting as <K...> string.

        Set the `defaults` argument `True` to additionally load default
        settings for all available settings. This is useful, when your list of
        configuration strings does not cover the full list of available
        settings.
        """
        # initialize instance with defaults
        instance = cls()

        if defaults:
            instance.load_defaults()

        for line in list_of_strings:
            match = cls._K_CODE_PATTERN.match(line)

            try:
                k_code = match.group(1)
            except (IndexError, AttributeError):
                # line did not start with K-code
                continue

            try:
                serializer = REGISTRY[k_code]
                prop_name = instance._clsname_to_propname(serializer.__name__)
                setattr(
                    instance, prop_name, serializer.from_config_string(line))
            except KeyError:
                logger.info(
                    'Cannot find serializer class for K-code %s$' % k_code)

        return instance

    def _clsname_to_propname(self, clsname):
        """camelCase-to-under_score string conversion

        Used to convert serializer class names to property names when
        dynamically setting or getting configuration properties.
        """
        return re.sub(r'([a-z])([A-Z])', r'\1_\2', clsname).lower()

    def to_config_string(self, separator=b''):
        """Serialized the object into a single string for sending to device

        Use the `separator` argument to specify any bytes that should appear
        between individual configuration settings. To output one setting per
        line, for example, specify `separator=b'\\n'`
        """
        props = [
            getattr(self, self._clsname_to_propname(prop.__name__), None)
            for prop in REGISTRY.values()
        ]
        return separator.join([
            prop.to_config_string() for prop in props if prop])
