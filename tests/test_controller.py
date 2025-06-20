"""Tests for controller module."""

from unittest.mock import Mock, patch

import pytest

from pycompool.controller import PoolController
from pycompool.protocol import (
    HEARTBEAT_DEST,
    HEARTBEAT_OPCODE,
    SYNC,
    calculate_checksum,
)


class TestPoolController:
    """Test PoolController class."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        controller = PoolController()
        assert controller.connection is not None
        assert controller.port == controller.connection.port
        assert controller.baud == controller.connection.baud

    def test_init_with_params(self):
        """Test initialization with parameters."""
        controller = PoolController("/dev/ttyUSB1", 19200)
        assert controller.connection.port == "/dev/ttyUSB1"
        assert controller.connection.baud == 19200

    @patch('pycompool.controller.SerialConnection')
    def test_set_pool_temperature_success(self, mock_connection_class, capsys):
        """Test successful pool temperature setting."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        controller = PoolController()
        result = controller.set_pool_temperature("80f")

        assert result is True
        mock_connection.send_packet.assert_called_once()

        # Check output
        captured = capsys.readouterr()
        assert "Pool set-point → 80.0 °F — ✓ ACK" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_set_pool_temperature_no_ack(self, mock_connection_class, capsys):
        """Test pool temperature setting with no ACK."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = False

        controller = PoolController()
        result = controller.set_pool_temperature("80f")

        assert result is False

        # Check output
        captured = capsys.readouterr()
        assert "Pool set-point → 80.0 °F — ✗ NO ACK" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_set_pool_temperature_celsius(self, mock_connection_class, capsys):
        """Test pool temperature setting with celsius."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        controller = PoolController()
        result = controller.set_pool_temperature("26.7c")

        assert result is True

        # Check output (should show fahrenheit conversion)
        captured = capsys.readouterr()
        assert "Pool set-point → 80.1 °F — ✓ ACK" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_set_pool_temperature_verbose(self, mock_connection_class, capsys):
        """Test pool temperature setting with verbose output."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        controller = PoolController()
        result = controller.set_pool_temperature("80f", verbose=True)

        assert result is True

        # Check verbose output shows packet hex
        captured = capsys.readouterr()
        assert "→" in captured.out  # Packet hex output
        assert "Pool set-point" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_set_spa_temperature_success(self, mock_connection_class, capsys):
        """Test successful spa temperature setting."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        controller = PoolController()
        result = controller.set_spa_temperature("104f")

        assert result is True
        mock_connection.send_packet.assert_called_once()

        # Check output
        captured = capsys.readouterr()
        assert "Spa set-point → 104.0 °F — ✓ ACK" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_set_spa_temperature_no_ack(self, mock_connection_class, capsys):
        """Test spa temperature setting with no ACK."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = False

        controller = PoolController()
        result = controller.set_spa_temperature("104f")

        assert result is False

        # Check output
        captured = capsys.readouterr()
        assert "Spa set-point → 104.0 °F — ✗ NO ACK" in captured.out

    def test_invalid_temperature_format(self):
        """Test invalid temperature format raises ValueError."""
        controller = PoolController()

        with pytest.raises(ValueError, match="temperature must look like"):
            controller.set_pool_temperature("hot")

        with pytest.raises(ValueError, match="temperature must look like"):
            controller.set_spa_temperature("80")

    @patch('pycompool.controller.SerialConnection')
    def test_packet_content_pool(self, mock_connection_class):
        """Test that pool temperature packet has correct content."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        controller = PoolController()
        controller.set_pool_temperature("80f")

        # Verify packet structure
        call_args = mock_connection.send_packet.call_args[0][0]
        assert len(call_args) == 17  # Command packet length
        assert call_args[:2] == b"\xFF\xAA"  # Sync bytes
        assert call_args[11] == 107  # 80F = 26.67C, encoded as 26.67*4 ≈ 107
        assert call_args[14] == 0x20  # Enable bit 5 for pool temp

    @patch('pycompool.controller.SerialConnection')
    def test_packet_content_spa(self, mock_connection_class):
        """Test that spa temperature packet has correct content."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        controller = PoolController()
        controller.set_spa_temperature("104f")

        # Verify packet structure
        call_args = mock_connection.send_packet.call_args[0][0]
        assert len(call_args) == 17  # Command packet length
        assert call_args[:2] == b"\xFF\xAA"  # Sync bytes
        assert call_args[12] == 160  # 104F = 40C, encoded as 40*4 = 160
        assert call_args[14] == 0x40  # Enable bit 6 for spa temp

    @patch('pycompool.controller.SerialConnection')
    def test_set_heater_mode_success(self, mock_connection_class, capsys):
        """Test successful heater mode setting."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        controller = PoolController()
        result = controller.set_heater_mode("heater", "pool")

        assert result is True
        mock_connection.send_packet.assert_called_once()

        # Check output
        captured = capsys.readouterr()
        assert "Pool heating → heater — ✓ ACK" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_set_heater_mode_no_ack(self, mock_connection_class, capsys):
        """Test heater mode setting with no ACK."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = False

        controller = PoolController()
        result = controller.set_heater_mode("solar-only", "spa")

        assert result is False

        # Check output
        captured = capsys.readouterr()
        assert "Spa heating → solar-only — ✗ NO ACK" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_set_heater_mode_verbose(self, mock_connection_class, capsys):
        """Test heater mode setting with verbose output."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        controller = PoolController()
        result = controller.set_heater_mode("off", "pool", verbose=True)

        assert result is True

        # Check verbose output shows packet hex
        captured = capsys.readouterr()
        assert "→" in captured.out  # Packet hex output
        assert "Pool heating → off" in captured.out

    def test_set_heater_mode_invalid_mode(self):
        """Test invalid heater mode raises ValueError."""
        controller = PoolController()

        with pytest.raises(ValueError, match="Invalid mode 'invalid'"):
            controller.set_heater_mode("invalid", "pool")

    def test_set_heater_mode_invalid_target(self):
        """Test invalid target raises ValueError."""
        controller = PoolController()

        with pytest.raises(ValueError, match="Invalid target 'jacuzzi'"):
            controller.set_heater_mode("heater", "jacuzzi")

    @patch('pycompool.controller.SerialConnection')
    def test_heater_mode_packet_content_pool(self, mock_connection_class):
        """Test that pool heater mode packet has correct content."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        controller = PoolController()

        # Test each mode for pool
        test_cases = [
            ("off", 0x00),           # 0b00 << 4 = 0x00
            ("heater", 0x10),        # 0b01 << 4 = 0x10
            ("solar-priority", 0x20), # 0b10 << 4 = 0x20
            ("solar-only", 0x30),    # 0b11 << 4 = 0x30
        ]

        for mode, expected_heat_source in test_cases:
            mock_connection.reset_mock()
            controller.set_heater_mode(mode, "pool")

            # Verify packet structure
            call_args = mock_connection.send_packet.call_args[0][0]
            assert len(call_args) == 17  # Command packet length
            assert call_args[:2] == b"\xFF\xAA"  # Sync bytes
            assert call_args[10] == expected_heat_source  # Heat source byte
            assert call_args[14] == 0x10  # Enable bit 4 for heat source

    @patch('pycompool.controller.SerialConnection')
    def test_heater_mode_packet_content_spa(self, mock_connection_class):
        """Test that spa heater mode packet has correct content."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        controller = PoolController()

        # Test each mode for spa
        test_cases = [
            ("off", 0x00),           # 0b00 << 6 = 0x00
            ("heater", 0x40),        # 0b01 << 6 = 0x40
            ("solar-priority", 0x80), # 0b10 << 6 = 0x80
            ("solar-only", 0xC0),    # 0b11 << 6 = 0xC0
        ]

        for mode, expected_heat_source in test_cases:
            mock_connection.reset_mock()
            controller.set_heater_mode(mode, "spa")

            # Verify packet structure
            call_args = mock_connection.send_packet.call_args[0][0]
            assert len(call_args) == 17  # Command packet length
            assert call_args[:2] == b"\xFF\xAA"  # Sync bytes
            assert call_args[10] == expected_heat_source  # Heat source byte
            assert call_args[14] == 0x10  # Enable bit 4 for heat source

    def test_properties(self):
        """Test controller properties."""
        controller = PoolController("/dev/ttyUSB1", 19200)
        assert controller.port == "/dev/ttyUSB1"
        assert controller.baud == 19200

    def _create_test_heartbeat(self):
        """Create a test heartbeat packet."""
        defaults = {
            'version': 0x01,
            'minutes': 0x1E,
            'hours': 0x0C,
            'primary_equip': 0x00,
            'secondary_equip': 0x00,
            'delay_heat_source': 0x00,
            'water_temp': 0x50,
            'solar_temp': 0x50,
            'spa_water_temp': 0x60,
            'spa_solar_temp': 0x60,
            'desired_pool_temp': 0x50,
            'desired_spa_temp': 0x60,
            'air_temp': 0x48,
        }

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

    @patch('pycompool.controller.SerialConnection')
    def test_get_status_success(self, mock_connection_class):
        """Test successful status retrieval."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection

        mock_packet = self._create_test_heartbeat()
        mock_connection.read_packets.return_value = iter([mock_packet])

        controller = PoolController()
        status = controller.get_status()

        assert status is not None
        assert 'pool_water_temp_f' in status
        assert 'spa_water_temp_f' in status
        mock_connection.read_packets.assert_called_once_with(packet_size=24, timeout=10.0)

    @patch('pycompool.controller.SerialConnection')
    def test_get_status_no_packet(self, mock_connection_class):
        """Test status retrieval with no packets received."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.read_packets.return_value = iter([])

        controller = PoolController()
        status = controller.get_status()

        assert status is None
        mock_connection.read_packets.assert_called_once_with(packet_size=24, timeout=10.0)

    @patch('pycompool.controller.SerialConnection')
    def test_get_status_custom_timeout(self, mock_connection_class):
        """Test status retrieval with custom timeout."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.read_packets.return_value = iter([])

        controller = PoolController()
        controller.get_status(timeout=5.0)

        mock_connection.read_packets.assert_called_once_with(packet_size=24, timeout=5.0)
