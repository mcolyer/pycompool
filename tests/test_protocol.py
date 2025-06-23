"""Tests for protocol module."""

import pytest

from pycompool.protocol import (
    HEARTBEAT_DEST,
    HEARTBEAT_OPCODE,
    SYNC,
    PacketType,
    byte_to_celsius,
    calculate_checksum,
    celsius_to_byte,
    celsius_to_fahrenheit,
    create_command_packet,
    parse_heartbeat_packet,
    tempstr_to_celsius,
)


class TestTemperatureConversion:
    """Test temperature conversion functions."""

    def test_tempstr_to_celsius_fahrenheit(self):
        """Test fahrenheit to celsius conversion."""
        assert tempstr_to_celsius("32f") == 0.0
        assert tempstr_to_celsius("212f") == 100.0
        assert tempstr_to_celsius("80f") == pytest.approx(26.67, abs=0.01)

    def test_tempstr_to_celsius_celsius(self):
        """Test celsius input passthrough."""
        assert tempstr_to_celsius("0c") == 0.0
        assert tempstr_to_celsius("100c") == 100.0
        assert tempstr_to_celsius("25.5c") == 25.5

    def test_tempstr_to_celsius_case_insensitive(self):
        """Test case insensitive input."""
        assert tempstr_to_celsius("80F") == tempstr_to_celsius("80f")
        assert tempstr_to_celsius("25C") == tempstr_to_celsius("25c")

    def test_tempstr_to_celsius_with_spaces(self):
        """Test input with whitespace."""
        assert tempstr_to_celsius(" 80 f ") == tempstr_to_celsius("80f")
        assert tempstr_to_celsius("  25.5 c  ") == 25.5

    def test_tempstr_to_celsius_invalid(self):
        """Test invalid input raises ValueError."""
        with pytest.raises(ValueError, match="temperature must look like"):
            tempstr_to_celsius("80")
        with pytest.raises(ValueError, match="temperature must look like"):
            tempstr_to_celsius("hot")
        with pytest.raises(ValueError, match="temperature must look like"):
            tempstr_to_celsius("80k")

    def test_celsius_to_byte(self):
        """Test celsius to byte encoding."""
        assert celsius_to_byte(0.0) == 0
        assert celsius_to_byte(25.0) == 100  # 25 * 4
        assert celsius_to_byte(40.0) == 160  # 40 * 4
        assert celsius_to_byte(63.75) == 255  # Max value

    def test_celsius_to_byte_bounds(self):
        """Test byte encoding bounds."""
        assert celsius_to_byte(-10.0) == 0  # Below minimum
        assert celsius_to_byte(300.0) == 255  # Above maximum

    def test_byte_to_celsius(self):
        """Test byte to celsius decoding."""
        assert byte_to_celsius(0) == 0.0
        assert byte_to_celsius(100) == 25.0  # 100 / 4
        assert byte_to_celsius(160) == 40.0  # 160 / 4
        assert byte_to_celsius(255) == 63.75  # 255 / 4

    def test_celsius_to_fahrenheit(self):
        """Test celsius to fahrenheit conversion."""
        assert celsius_to_fahrenheit(0.0) == 32.0
        assert celsius_to_fahrenheit(100.0) == 212.0
        assert celsius_to_fahrenheit(25.0) == 77.0


class TestChecksum:
    """Test checksum calculation."""

    def test_calculate_checksum(self):
        """Test checksum calculation."""
        data = b"\xFF\xAA\x00\x01\x82\x09"
        checksum = calculate_checksum(data)
        assert isinstance(checksum, int)
        assert 0 <= checksum <= 0xFFFF

    def test_calculate_checksum_consistency(self):
        """Test checksum is consistent."""
        data = b"\xFF\xAA\x00\x01\x82\x09"
        checksum1 = calculate_checksum(data)
        checksum2 = calculate_checksum(data)
        assert checksum1 == checksum2


class TestPacketCreation:
    """Test packet creation functions."""

    def test_create_command_packet(self):
        """Test command packet creation."""
        packet = create_command_packet(
            pool_temp=100,
            spa_temp=160,
            enable_bits=0x60  # Enable pool and spa temps
        )

        assert len(packet) == 17
        assert packet[:2] == SYNC
        assert packet[8] == 0     # Primary equip
        assert packet[11] == 100  # Pool temp
        assert packet[12] == 160  # Spa temp
        assert packet[14] == 0x60  # Enable bits

    def test_create_command_packet_defaults(self):
        """Test command packet with default values."""
        packet = create_command_packet()

        assert len(packet) == 17
        assert packet[:2] == SYNC
        assert packet[8] == 0   # Primary equip
        assert packet[11] == 0  # Pool temp
        assert packet[12] == 0  # Spa temp
        assert packet[14] == 0  # Enable bits

    def test_create_command_packet_with_primary_equip(self):
        """Test command packet with primary equipment control."""
        packet = create_command_packet(
            primary_equip=0x14,  # aux3 and aux5 on (bits 2 and 4)
            enable_bits=0x01     # Enable primary equip field
        )

        assert len(packet) == 17
        assert packet[:2] == SYNC
        assert packet[8] == 0x14  # Primary equip byte
        assert packet[14] == 0x01  # Enable bits


class TestHeartbeatParsing:
    """Test heartbeat packet parsing."""

    def create_test_heartbeat(self, **kwargs):
        """Create a test heartbeat packet."""
        defaults = {
            'version': 0x10,
            'minutes': 30,
            'hours': 14,
            'primary_equip': 0x03,
            'secondary_equip': 0x0A,
            'delay_heat_source': 0x00,
            'water_temp': 100,  # 25°C
            'solar_temp': 80,   # 40°C
            'spa_water_temp': 160,  # 40°C
            'spa_solar_temp': 90,   # 45°C
            'desired_pool_temp': 120,  # 30°C
            'desired_spa_temp': 168,   # 42°C
            'air_temp': 60,  # 30°C
        }
        defaults.update(kwargs)

        # Build packet
        packet = bytearray(24)
        packet[:2] = SYNC
        packet[2] = HEARTBEAT_DEST
        packet[3] = defaults['version']
        packet[4] = HEARTBEAT_OPCODE
        packet[5] = 0x10  # Info length
        packet[6] = defaults['minutes']
        packet[7] = defaults['hours']
        packet[8] = defaults['primary_equip']
        packet[9] = defaults['secondary_equip']
        packet[10] = defaults['delay_heat_source']
        packet[11] = defaults['water_temp']
        packet[12] = defaults['solar_temp']
        packet[13] = defaults['spa_water_temp']
        packet[14] = defaults['spa_solar_temp']
        packet[15] = defaults['desired_pool_temp']
        packet[16] = defaults['desired_spa_temp']
        packet[17] = defaults['air_temp']
        packet[18] = 0  # Spare
        packet[19] = 0  # Spare
        packet[20] = 0  # Equipment status
        packet[21] = 0  # Product type

        # Calculate and add checksum
        checksum = calculate_checksum(packet[:-2])
        packet[22] = (checksum >> 8) & 0xFF
        packet[23] = checksum & 0xFF

        return bytes(packet)

    def test_parse_valid_heartbeat(self):
        """Test parsing a valid heartbeat packet."""
        packet = self.create_test_heartbeat()
        parsed = parse_heartbeat_packet(packet)

        assert parsed is not None
        assert parsed['type'] == PacketType.HEARTBEAT
        assert parsed['version'] == 0x10
        assert parsed['time'] == "14:30"
        assert parsed['pool_water_temp'] == 25.0
        assert parsed['spa_water_temp'] == 40.0
        assert parsed['desired_pool_temp'] == 30.0
        assert parsed['desired_spa_temp'] == 42.0

        # Test auxiliary equipment parsing (3820 system layout)
        assert parsed['aux1_on'] is True     # Bit 0 of 0x03
        assert parsed['aux2_on'] is True     # Bit 1 of 0x03
        assert parsed['aux3_on'] is False    # Bit 2 of 0x03
        assert parsed['aux4_on'] is False    # Bit 3 of 0x03
        assert parsed['aux5_on'] is False    # Bit 4 of 0x03
        assert parsed['aux6_on'] is False    # Bit 5 of 0x03
        assert parsed['aux7_on'] is False    # Bit 6 of 0x03
        assert parsed['aux8_on'] is False    # Bit 7 of 0x03

    def test_parse_heartbeat_status_flags(self):
        """Test parsing status flags from secondary equipment byte."""
        # Test with heater and solar on
        packet = self.create_test_heartbeat(secondary_equip=0x06)  # Bits 1,2
        parsed = parse_heartbeat_packet(packet)

        assert parsed['heater_on'] is True
        assert parsed['solar_on'] is True
        assert parsed['service_mode'] is False
        assert parsed['freeze_mode'] is False

    def test_parse_heartbeat_aux_equipment(self):
        """Test parsing auxiliary equipment from primary equipment byte."""
        # Test with aux3 and aux5 on (bits 2 and 4)
        packet = self.create_test_heartbeat(primary_equip=0x14)  # 0x14 = 0b00010100
        parsed = parse_heartbeat_packet(packet)

        assert parsed['aux1_on'] is False    # Bit 0
        assert parsed['aux2_on'] is False    # Bit 1
        assert parsed['aux3_on'] is True     # Bit 2
        assert parsed['aux4_on'] is False    # Bit 3
        assert parsed['aux5_on'] is True     # Bit 4
        assert parsed['aux6_on'] is False    # Bit 5
        assert parsed['aux7_on'] is False    # Bit 6
        assert parsed['aux8_on'] is False    # Bit 7

    def test_parse_heartbeat_invalid_sync(self):
        """Test parsing with invalid sync bytes."""
        packet = self.create_test_heartbeat()
        packet = b"\x00\x00" + packet[2:]  # Invalid sync

        assert parse_heartbeat_packet(packet) is None

    def test_parse_heartbeat_wrong_opcode(self):
        """Test parsing with wrong opcode."""
        packet = bytearray(self.create_test_heartbeat())
        packet[4] = 0x01  # Wrong opcode

        assert parse_heartbeat_packet(bytes(packet)) is None

    def test_parse_heartbeat_bad_checksum(self):
        """Test parsing with bad checksum."""
        packet = bytearray(self.create_test_heartbeat())
        packet[22] = 0xFF  # Bad checksum
        packet[23] = 0xFF

        assert parse_heartbeat_packet(bytes(packet)) is None

    def test_parse_heartbeat_too_short(self):
        """Test parsing packet that's too short."""
        packet = self.create_test_heartbeat()[:20]  # Truncated

        assert parse_heartbeat_packet(packet) is None
