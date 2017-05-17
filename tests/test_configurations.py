from unittest import TestCase

from microscan import config


class TestHostPortConnectionSerializer(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K100,6,1,0,1>'
        obj = config.HostPortConnection.from_config_string(str_)
        self.assertEqual(obj.baud_rate, 38400)
        self.assertEqual(obj.parity, config.Parity.EVEN)
        self.assertEqual(obj.stop_bits, config.StopBits.ONE)
        self.assertEqual(obj.data_bits, config.DataBits.EIGHT)

    def test_deserialization_2(self):
        str_ = b'<K100,4,0,1,0>'
        obj = config.HostPortConnection.from_config_string(str_)
        self.assertEqual(obj.baud_rate, 9600)
        self.assertEqual(obj.parity, config.Parity.NONE)
        self.assertEqual(obj.stop_bits, config.StopBits.TWO)
        self.assertEqual(obj.data_bits, config.DataBits.SEVEN)

    def test_deserialization_3(self):
        str_ = b'<K100,0,2,1,0>'
        obj = config.HostPortConnection.from_config_string(str_)
        self.assertEqual(obj.baud_rate, 600)
        self.assertEqual(obj.parity, config.Parity.ODD)
        self.assertEqual(obj.stop_bits, config.StopBits.TWO)
        self.assertEqual(obj.data_bits, config.DataBits.SEVEN)

    def test_serialization_1(self):
        obj = config.HostPortConnection(
            baud_rate=9600,
            parity=config.Parity.EVEN,
            stop_bits=config.StopBits.ONE,
            data_bits=config.DataBits.SEVEN,
        )
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K100,4,1,0,0>')


class TestHostProtocolSerializer(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K140,4>'
        obj = config.HostProtocol.from_config_string(str_)
        self.assertEqual(obj.protocol, config.Protocol.PollingModeD)

    def test_deserialization_2(self):
        str_ = b'<K140,0>'
        obj = config.HostProtocol.from_config_string(str_)
        self.assertEqual(obj.protocol, config.Protocol.PointToPoint)

    def test_serialization_1(self):
        obj = config.HostProtocol(protocol=config.Protocol.PollingModeD)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K140,4>')


class TestHostRS422Status(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K102,1>'
        obj = config.HostRS422Status.from_config_string(str_)
        self.assertEqual(obj.status, config.RS422Status.Enabled)

    def test_serialization_1(self):
        obj = config.HostRS422Status(status=config.RS422Status.Disabled)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K102,0>')

    def test_serialization_2(self):
        obj = config.HostRS422Status(status=config.RS422Status.Enabled)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K102,1>')


class TestRS232AuxiliaryPort(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K101,2,3,1,1,0,1,AB>'
        obj = config.RS232AuxiliaryPort.from_config_string(str_)
        self.assertEqual(
            obj.aux_port_mode, config.AuxiliaryPortMode.HalfDuplex)
        self.assertEqual(obj.baud_rate, 4800)
        self.assertEqual(obj.parity, config.Parity.EVEN)
        self.assertEqual(obj.stop_bits, config.StopBits.TWO)
        self.assertEqual(obj.data_bits, config.DataBits.SEVEN)
        self.assertEqual(
            obj.daisy_chain_id_status, config.DaisyChainIdStatus.Enabled)
        self.assertEqual(obj.daisy_chain_id, b'AB')

    def test_deserialization_2(self):
        str_ = b'<K101,1,5,2,0,1,0,>'
        obj = config.RS232AuxiliaryPort.from_config_string(str_)
        self.assertEqual(
            obj.aux_port_mode, config.AuxiliaryPortMode.Transparent)
        self.assertEqual(obj.baud_rate, 19200)
        self.assertEqual(obj.parity, config.Parity.ODD)
        self.assertEqual(obj.stop_bits, config.StopBits.ONE)
        self.assertEqual(obj.data_bits, config.DataBits.EIGHT)
        self.assertEqual(
            obj.daisy_chain_id_status, config.DaisyChainIdStatus.Disabled)
        self.assertEqual(obj.daisy_chain_id, None)

    def test_serialization_1(self):
        obj = config.RS232AuxiliaryPort(
            aux_port_mode=config.AuxiliaryPortMode.HalfDuplex,
            baud_rate=600,
            parity=config.Parity.NONE,
            stop_bits=config.StopBits.TWO,
            data_bits=config.DataBits.SEVEN,
            daisy_chain_id_status=config.DaisyChainIdStatus.Disabled,
            daisy_chain_id='',
        )
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K101,2,0,0,1,0,0,>')


class TestPreamble(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K141,0,>'
        obj = config.Preamble.from_config_string(str_)
        self.assertEqual(obj.status, config.PreambleStatus.Disabled)
        self.assertEqual(obj.characters, None)

    def test_deserialization_2(self):
        str_ = b'<K141,1,12AB>'
        obj = config.Preamble.from_config_string(str_)
        self.assertEqual(obj.status, config.PreambleStatus.Enabled)
        self.assertEqual(obj.characters, b'12AB')

    def test_serialization_1(self):
        obj = config.Preamble(status=config.PreambleStatus.Disabled)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K141,0,>')

    def test_serialization_2(self):
        obj = config.Preamble(
            status=config.PreambleStatus.Enabled, characters='XYZ')
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K141,1,XYZ>')


class TestPostamble(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K142,0,>'
        obj = config.Postamble.from_config_string(str_)
        self.assertEqual(obj.status, config.PostambleStatus.Disabled)
        self.assertEqual(obj.characters, None)

    def test_deserialization_2(self):
        str_ = b'<K142,1,12AB>'
        obj = config.Postamble.from_config_string(str_)
        self.assertEqual(obj.status, config.PostambleStatus.Enabled)
        self.assertEqual(obj.characters, b'12AB')

    def test_serialization_1(self):
        obj = config.Postamble(status=config.PostambleStatus.Disabled)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K142,0,>')

    def test_serialization_2(self):
        obj = config.Postamble(
            status=config.PostambleStatus.Enabled, characters='XYZ')
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K142,1,XYZ>')


class TestLRC(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K145,1>'
        obj = config.LRC.from_config_string(str_)
        self.assertEqual(obj.status, config.LRCStatus.Enabled)

    def test_serialization_1(self):
        obj = config.LRC(status=config.LRCStatus.Disabled)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K145,0>')


class TestInterCharacterDelay(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K144,123>'
        obj = config.InterCharacterDelay.from_config_string(str_)
        self.assertEqual(obj.delay, 123)

    def test_serialization_1(self):
        obj = config.InterCharacterDelay(delay=42)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K144,42>')


class TestMultisymbol(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K222,2,|>'
        obj = config.Multisymbol.from_config_string(str_)
        self.assertEqual(obj.number_of_symbols, 2)
        self.assertEqual(obj.multisymbol_separator, b'|')

    def test_deserialization_2(self):
        str_ = b'<K222,1,>'
        obj = config.Multisymbol.from_config_string(str_)
        self.assertEqual(obj.number_of_symbols, 1)
        self.assertEqual(obj.multisymbol_separator, None)

    def test_serialization_1(self):
        obj = config.Multisymbol(
            number_of_symbols=3, multisymbol_separator='+')
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K222,3,+>')

    def test_serialization_2(self):
        obj = config.Multisymbol(
            number_of_symbols=1, multisymbol_separator=None)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K222,1,>')


class TestTrigger(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K200,0,244>'
        obj = config.Trigger.from_config_string(str_)
        self.assertEqual(obj.trigger_mode, config.TriggerMode.ContinuousRead)
        self.assertEqual(obj.trigger_filter_duration, 244)

    def test_deserialization_2(self):
        str_ = b'<K200,3,9999>'
        obj = config.Trigger.from_config_string(str_)
        self.assertEqual(obj.trigger_mode, config.TriggerMode.ExternalEdge)
        self.assertEqual(obj.trigger_filter_duration, 9999)

    def test_serialization_1(self):
        obj = config.Trigger(
            trigger_mode=config.TriggerMode.SerialData,
            trigger_filter_duration=245)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K200,4,245>')


class TestExternalTrigger(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K202,0>'
        obj = config.ExternalTrigger.from_config_string(str_)
        self.assertEqual(
            obj.external_trigger_state, config.ExternalTriggerState.Negative)

    def test_serialization_1(self):
        obj = config.ExternalTrigger(
            external_trigger_state=config.ExternalTriggerState.Positive)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K202,1>')


class TestSerialTrigger(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K201,=>'
        obj = config.SerialTrigger.from_config_string(str_)
        self.assertEqual(obj.serial_trigger_character, b'=')

    def test_serialization_1(self):
        obj = config.SerialTrigger(serial_trigger_character=b't')
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K201,t>')


class TestStartTriggerCharacter(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K229,>'
        obj = config.StartTriggerCharacter.from_config_string(str_)
        self.assertEqual(obj.start_trigger_character, None)

    def test_deserialization_2(self):
        str_ = b'<K229,01>'
        obj = config.StartTriggerCharacter.from_config_string(str_)
        self.assertEqual(obj.start_trigger_character, b'01')

    def test_serialization_1(self):
        obj = config.StartTriggerCharacter(start_trigger_character=None)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K229,>')

    def test_serialization_2(self):
        obj = config.StartTriggerCharacter(start_trigger_character='88')
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K229,88>')


class TestStopTriggerCharacter(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K230,>'
        obj = config.StopTriggerCharacter.from_config_string(str_)
        self.assertEqual(obj.stop_trigger_character, None)

    def test_deserialization_2(self):
        str_ = b'<K230,02>'
        obj = config.StopTriggerCharacter.from_config_string(str_)
        self.assertEqual(obj.stop_trigger_character, b'02')

    def test_serialization_1(self):
        obj = config.StopTriggerCharacter(stop_trigger_character=None)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K230,>')

    def test_serialization_2(self):
        obj = config.StopTriggerCharacter(stop_trigger_character='99')
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K230,99>')


class TestEndReadCycle(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K220,2,100>'
        obj = config.EndReadCycle.from_config_string(str_)
        self.assertEqual(
            obj.end_read_cycle_mode,
            config.EndReadCycleMode.TimeoutAndNewTrigger)
        self.assertEqual(obj.ready_cycle_timeout, 100)

    def test_deserialization_2(self):
        str_ = b'<K220,0,65535>'
        obj = config.EndReadCycle.from_config_string(str_)
        self.assertEqual(
            obj.end_read_cycle_mode, config.EndReadCycleMode.Timeout)
        self.assertEqual(obj.ready_cycle_timeout, 65535)

    def test_serialization_1(self):
        obj = config.EndReadCycle(
            end_read_cycle_mode=config.EndReadCycleMode.Timeout,
            read_cycle_timeout=1234)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K220,0,1234>')


class TestDecodesBeforeOutput(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K221,100,1>'
        obj = config.DecodesBeforeOutput.from_config_string(str_)
        self.assertEqual(obj.number_before_output, 100)
        self.assertEqual(
            obj.decodes_before_output_mode,
            config.DecodesBeforeOutputMode.Consecutive)

    def test_deserialization_2(self):
        str_ = b'<K221,255,0>'
        obj = config.DecodesBeforeOutput.from_config_string(str_)
        self.assertEqual(obj.number_before_output, 255)
        self.assertEqual(
            obj.decodes_before_output_mode,
            config.DecodesBeforeOutputMode.NonConsecutive)

    def test_serialization_1(self):
        obj = config.DecodesBeforeOutput(
            number_before_output=20,
            decodes_before_output_mode=(
                config.DecodesBeforeOutputMode.Consecutive))
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K221,20,1>')


class TestScanSpeed(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K500,45>'
        obj = config.ScanSpeed.from_config_string(str_)
        self.assertEqual(obj.scan_speed, 45)

    def test_serialization_1(self):
        obj = config.ScanSpeed(scan_speed=55)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K500,55>')


class TestScannerSetup(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K504,50,2,60,230>'
        obj = config.ScannerSetup.from_config_string(str_)
        self.assertEqual(obj.gain_level, 50)
        self.assertEqual(
            obj.agc_sampling_mode, config.AGCSamplingMode.Continuous)
        self.assertEqual(obj.agc_min, 60)
        self.assertEqual(obj.agc_max, 230)

    def test_deserialization_2(self):
        str_ = b'<K504,80,1,120,255>'
        obj = config.ScannerSetup.from_config_string(str_)
        self.assertEqual(obj.gain_level, 80)
        self.assertEqual(
            obj.agc_sampling_mode, config.AGCSamplingMode.LeadingEdge)
        self.assertEqual(obj.agc_min, 120)
        self.assertEqual(obj.agc_max, 255)

    def test_serialization_1(self):
        obj = config.ScannerSetup(
            gain_level=90,
            agc_sampling_mode=config.AGCSamplingMode.Disabled,
            agc_min=None,
            agc_max=None,
        )
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K504,90,0,,>')

    def test_serialization_2(self):
        obj = config.ScannerSetup(
            gain_level=91,
            agc_sampling_mode=config.AGCSamplingMode.Continuous,
            agc_min=111,
            agc_max=222,
        )
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K504,91,2,111,222>')


class TestSymbolDetect(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K505,1,15>'
        obj = config.SymbolDetect.from_config_string(str_)
        self.assertEqual(obj.status, config.SymbolDetectStatus.Enabled)
        self.assertEqual(obj.transition_counter, 15)

    def test_serialization_1(self):
        obj = config.SymbolDetect(
            status=config.SymbolDetectStatus.Disabled, transition_counter=None)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K505,0,>')

    def test_serialization_2(self):
        obj = config.SymbolDetect(
            status=config.SymbolDetectStatus.Enabled, transition_counter=99)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K505,1,99>')


class TestMaximumElement(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K502,123>'
        obj = config.MaximumElement.from_config_string(str_)
        self.assertEqual(obj.maximum_element, 123)

    def test_serialization_1(self):
        obj = config.MaximumElement(maximum_element=65534)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K502,65534>')


class TestScanWidthEnhance(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K511,0>'
        obj = config.ScanWidthEnhance.from_config_string(str_)
        self.assertEqual(obj.status, config.ScanWidthEnhanceStatus.Disabled)

    def test_serialization_1(self):
        obj = config.ScanWidthEnhance(
            status=config.ScanWidthEnhanceStatus.Enabled)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K511,1>')


class TestLaserSetup(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K700,1,1,10,95,1>'
        obj = config.LaserSetup.from_config_string(str_)
        self.assertEqual(
            obj.laser_on_off_status, config.LaserOnOffStatus.Enabled)
        self.assertEqual(
            obj.laser_framing_status, config.LaserFramingStatus.Enabled)
        self.assertEqual(obj.laser_on_position, 10)
        self.assertEqual(obj.laser_off_position, 95)
        self.assertEqual(obj.laser_power, config.LaserPower.Medium)

    def test_deserialization_2(self):
        str_ = b'<K700,1,0,20,60,2>'
        obj = config.LaserSetup.from_config_string(str_)
        self.assertEqual(
            obj.laser_on_off_status, config.LaserOnOffStatus.Enabled)
        self.assertEqual(
            obj.laser_framing_status, config.LaserFramingStatus.Disabled)
        self.assertEqual(obj.laser_on_position, 20)
        self.assertEqual(obj.laser_off_position, 60)
        self.assertEqual(obj.laser_power, config.LaserPower.High)

    def test_serialization_1(self):
        obj = config.LaserSetup(
            laser_on_off_status=config.LaserOnOffStatus.Enabled,
            laser_framing_status=config.LaserFramingStatus.Enabled,
            laser_on_position=35,
            laser_off_position=55,
            laser_power=config.LaserPower.High,
        )
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K700,1,1,35,55,2>')


class TestCode39(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K470,1,0,0,1,1,32,0>'
        obj = config.Code39.from_config_string(str_)
        self.assertEqual(obj.status, config.Code39Status.Enabled)
        self.assertEqual(
            obj.check_digit_status, config.CheckDigitStatus.Disabled)
        self.assertEqual(
            obj.check_digit_output, config.CheckDigitOutputStatus.Disabled)
        self.assertEqual(
            obj.large_intercharacter_gap,
            config.LargeInterCharacterStatus.Enabled)
        self.assertEqual(
            obj.fixed_symbol_length, config.FixedSymbolLengthStatus.Enabled)
        self.assertEqual(obj.symbol_length, 32)
        self.assertEqual(
            obj.full_ascii_set, config.FullASCIISetStatus.Disabled)

    def test_deserialization_2(self):
        str_ = b'<K470,1,1,1,0,0,1,1>'
        obj = config.Code39.from_config_string(str_)
        self.assertEqual(obj.status, config.Code39Status.Enabled)
        self.assertEqual(
            obj.check_digit_status, config.CheckDigitStatus.Enabled)
        self.assertEqual(
            obj.check_digit_output, config.CheckDigitOutputStatus.Enabled)
        self.assertEqual(
            obj.large_intercharacter_gap,
            config.LargeInterCharacterStatus.Disabled)
        self.assertEqual(
            obj.fixed_symbol_length, config.FixedSymbolLengthStatus.Disabled)
        self.assertEqual(obj.symbol_length, 1)
        self.assertEqual(
            obj.full_ascii_set, config.FullASCIISetStatus.Enabled)

    def test_serialization_1(self):
        obj = config.Code39(
            status=config.Code39Status.Enabled,
            check_digit_status=config.CheckDigitStatus.Disabled,
            check_digit_output=config.CheckDigitOutputStatus.Disabled,
            large_intercharacter_gap=config.LargeInterCharacterStatus.Disabled,
            fixed_symbol_length=config.FixedSymbolLengthStatus.Enabled,
            symbol_length=64,
            full_ascii_set=config.FullASCIISetStatus.Enabled,
        )
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K470,1,0,0,0,1,64,1>')


class TestCode128(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K474,1,0,10,1,0,0,,,0,0>'
        obj = config.Code128.from_config_string(str_)
        self.assertEqual(obj.status, config.Code128Status.Enabled)
        self.assertEqual(
            obj.fixed_symbol_length_status,
            config.FixedSymbolLengthStatus.Disabled)
        self.assertEqual(obj.symbol_length, 10)
        self.assertEqual(obj.ean128_status, config.EAN128Status.Enabled)
        self.assertEqual(
            obj.output_format, config.Code128OutputFormat.Standard)
        self.assertEqual(
            obj.application_record_separator_status,
            config.ApplicationRecordSeparatorStatus.Disabled)
        self.assertEqual(obj.application_record_separator_character, b',')
        self.assertEqual(
            obj.application_record_brackets,
            config.ApplicationRecordBrackets.Disabled)
        self.assertEqual(
            obj.application_record_padding,
            config.ApplicationRecordPadding.Disabled)

    def test_serialization_1(self):
        obj = config.Code128(
            status=config.Code128Status.Enabled,
            fixed_symbol_length_status=config.FixedSymbolLengthStatus.Enabled,
            symbol_length=42,
            ean128_status=config.EAN128Status.Disabled,
            output_format=config.Code128OutputFormat.Standard,
            application_record_separator_status=(
                config.ApplicationRecordSeparatorStatus.Disabled),
            application_record_separator_character=b'&',
            application_record_brackets=(
                config.ApplicationRecordBrackets.Enabled),
            application_record_padding=(
                config.ApplicationRecordPadding.Enabled),
        )
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K474,1,1,42,0,0,0,&,1,1>')


class TestInterleaved2Of5(TestCase):
    # TODO
    pass


class TestCodabar(TestCase):
    # TODO
    pass


class TestUPC_EAN(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K473,1,0,0,0,,,,0,0>'
        obj = config.UPC_EAN.from_config_string(str_)
        self.assertEqual(obj.upc_status, config.UPCStatus.Enabled)
        self.assertEqual(obj.ean_status, config.EANStatus.Disabled)
        self.assertEqual(
            obj.supplementals_status, config.SupplementalsStatus.Disabled)
        self.assertEqual(
            obj.separator_status, config.SeparatorStatus.Disabled)
        self.assertEqual(obj.separator_character, b',')
        self.assertEqual(
            obj.upc_e_output_to_upc_a, config.UPC_EoutputAsUPC_A.Disabled)
        self.assertEqual(obj.undocumented_field, 0)

    def test_deserialization_2(self):
        str_ = b'<K473,0,1,2,1,|,,1,0>'
        obj = config.UPC_EAN.from_config_string(str_)
        self.assertEqual(obj.upc_status, config.UPCStatus.Disabled)
        self.assertEqual(obj.ean_status, config.EANStatus.Enabled)
        self.assertEqual(
            obj.supplementals_status, config.SupplementalsStatus.Required)
        self.assertEqual(
            obj.separator_status, config.SeparatorStatus.Enabled)
        self.assertEqual(obj.separator_character, b'|')
        self.assertEqual(
            obj.upc_e_output_to_upc_a, config.UPC_EoutputAsUPC_A.Enabled)
        self.assertEqual(obj.undocumented_field, 0)

    def test_serialization_1(self):
        obj = config.UPC_EAN(
            upc_status=config.UPCStatus.Enabled,
            ean_status=config.EANStatus.Enabled,
            supplementals_status=config.SupplementalsStatus.Disabled,
            separator_status=config.SeparatorStatus.Enabled,
            separator_character='!',
            upc_e_output_to_upc_a=config.UPC_EoutputAsUPC_A.Disabled,
            undocumented_field=0,
        )
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K473,1,1,0,1,!,,0,0>')


class TestCode93(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K475,1,0,10>'
        obj = config.Code93.from_config_string(str_)
        self.assertEqual(obj.status, config.Code93Status.Enabled)
        self.assertEqual(
            obj.fixed_symbol_length_status,
            config.FixedSymbolLengthStatus.Disabled)
        self.assertEqual(obj.fixed_symbol_length, 10)

    def test_deserialization_2(self):
        str_ = b'<K475,1,1,5>'
        obj = config.Code93.from_config_string(str_)
        self.assertEqual(obj.status, config.Code93Status.Enabled)
        self.assertEqual(
            obj.fixed_symbol_length_status,
            config.FixedSymbolLengthStatus.Enabled)
        self.assertEqual(obj.fixed_symbol_length, 5)

    def test_serialization_1(self):
        obj = config.Code93(
            status=config.Code93Status.Enabled,
            fixed_symbol_length_status=config.FixedSymbolLengthStatus.Enabled,
            fixed_symbol_length=32,
        )
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K475,1,1,32>')


class TestPharmacode(TestCase):
    # TODO
    pass


class TestNarrowMarginsAndSymbologyID(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K450,1,0>'
        obj = config.NarrowMarginsAndSymbologyID.from_config_string(str_)
        self.assertEqual(
            obj.narrow_margins_status, config.NarrowMarginsStatus.Enabled)
        self.assertEqual(
            obj.symbology_id_status, config.SymbologyIDStatus.Disabled)

    def test_serialization_1(self):
        obj = config.NarrowMarginsAndSymbologyID(
            narrow_margins_status=config.NarrowMarginsStatus.Disabled,
            symbology_id_status=config.SymbologyIDStatus.Enabled)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K450,0,1>')


class TestColor(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K451,1>'
        obj = config.BackgroundColor.from_config_string(str_)
        self.assertEqual(obj.color, config.Color.Black)

    def test_serialization_1(self):
        obj = config.BackgroundColor(color=config.Color.White)
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K451,0>')


class TestSymbolRatioMode(TestCase):
    def test_deserialization_1(self):
        str_ = b'<K452,1,2,0,1>'
        obj = config.SymbolRatioMode.from_config_string(str_)
        self.assertEqual(obj.code39, config.SymbolRatio.Standard)
        self.assertEqual(obj.codabar, config.SymbolRatio.Aggressive)
        self.assertEqual(obj.interleaved_2_of_5, config.SymbolRatio.Tight)
        self.assertEqual(obj.code93, config.SymbolRatio.Standard)

        str_ = b'<K452,0,2,1,0>'
        obj = config.SymbolRatioMode.from_config_string(str_)
        self.assertEqual(obj.code39, config.SymbolRatio.Tight)
        self.assertEqual(obj.codabar, config.SymbolRatio.Aggressive)
        self.assertEqual(obj.interleaved_2_of_5, config.SymbolRatio.Standard)
        self.assertEqual(obj.code93, config.SymbolRatio.Tight)

    def test_serialization_1(self):
        obj = config.SymbolRatioMode(
            code39=config.SymbolRatio.Aggressive,
            codabar=config.SymbolRatio.Tight,
            interleaved_2_of_5=config.SymbolRatio.Aggressive,
            code93=config.SymbolRatio.Standard,
        )
        str_ = obj.to_config_string()
        self.assertEqual(str_, b'<K452,2,0,2,1>')
