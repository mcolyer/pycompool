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
        # Mock get_status to return a status with heat source byte
        controller.get_status = Mock(return_value={'delay_heat_source_byte': 0x00})
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
        # Mock get_status to return a status with heat source byte
        controller.get_status = Mock(return_value={'delay_heat_source_byte': 0x00})
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
        # Mock get_status to return a status with heat source byte
        controller.get_status = Mock(return_value={'delay_heat_source_byte': 0x00})
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
        # Mock get_status to return a status with heat source byte
        controller.get_status = Mock(return_value={'delay_heat_source_byte': 0x00})

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
        # Mock get_status to return a status with heat source byte
        controller.get_status = Mock(return_value={'delay_heat_source_byte': 0x00})

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

    @patch('pycompool.controller.SerialConnection')
    def test_set_aux_equipment_success(self, mock_connection_class, capsys):
        """Test successful auxiliary equipment control."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        # Mock get_status to return current state
        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.return_value = {'aux1_on': False}  # Aux1 currently OFF

            controller = PoolController()
            result = controller.set_aux_equipment(1, True)

            assert result is True
            mock_connection.send_packet.assert_called_once()

            # Check output (new format shows current → desired)
            captured = capsys.readouterr()
            assert "Aux1 OFF → ON — ✓ ACK" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_set_aux_equipment_failure(self, mock_connection_class, capsys):
        """Test failed auxiliary equipment control."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = False

        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.return_value = {'aux1_on': True}  # Aux1 currently ON

            controller = PoolController()
            result = controller.set_aux_equipment(1, False)

            assert result is False

            # Check output (toggle command sent but failed)
            captured = capsys.readouterr()
            assert "Aux1 ON → OFF — ✗ NO ACK" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_set_aux_equipment_verbose(self, mock_connection_class, capsys):
        """Test auxiliary equipment control with verbose output."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.return_value = {'aux2_on': False}  # Aux2 currently OFF

            controller = PoolController()
            result = controller.set_aux_equipment(2, True, verbose=True)

            assert result is True

            # Check verbose output shows packet hex
            captured = capsys.readouterr()
            assert "→" in captured.out  # Packet hex output
            assert "Aux2 OFF → ON" in captured.out

    def test_set_aux_equipment_invalid_aux_number(self):
        """Test invalid aux number raises ValueError."""
        controller = PoolController()

        with pytest.raises(ValueError, match="Invalid aux number '0'. Must be 1-8."):
            controller.set_aux_equipment(0, True)

        with pytest.raises(ValueError, match="Invalid aux number '9'. Must be 1-8."):
            controller.set_aux_equipment(9, True)

    @patch('pycompool.controller.SerialConnection')
    def test_aux_equipment_packet_content(self, mock_connection_class):
        """Test that aux equipment packet has correct content for toggle command."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        with patch.object(PoolController, 'get_status') as mock_status:
            # Mock aux1 as OFF, so turning it ON will send toggle command
            mock_status.return_value = {'aux1_on': False}

            controller = PoolController()

            # Test turning on aux1 - should send toggle since it's currently OFF
            controller.set_aux_equipment(1, True)

            # Verify packet structure - should only set bit 0 for aux1 toggle
            call_args = mock_connection.send_packet.call_args[0][0]
            assert len(call_args) == 17  # Command packet length
            assert call_args[:2] == b"\xFF\xAA"  # Sync bytes
            assert call_args[8] == 0x01  # Primary equip byte (bit 0 set for aux1)
            assert call_args[14] == 0x04  # Enable bit 2 for primary equip

    @patch('pycompool.controller.SerialConnection')
    def test_aux_equipment_no_op_when_already_in_desired_state(self, mock_connection_class):
        """Test that aux equipment doesn't send command when already in desired state."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        with patch.object(PoolController, 'get_status') as mock_status:
            # Mock aux1 as already ON
            mock_status.return_value = {'aux1_on': True}

            controller = PoolController()

            # Try to turn on aux1 when it's already on - should be no-op
            result = controller.set_aux_equipment(1, True)

            # Should return True but not send any packet
            assert result is True
            mock_connection.send_packet.assert_not_called()

    @patch('pycompool.controller.SerialConnection')
    def test_aux_equipment_toggle_method(self, mock_connection_class):
        """Test that toggle_aux_equipment always sends toggle command."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        with patch.object(PoolController, '_check_service_mode') as mock_service:
            mock_service.return_value = False

            controller = PoolController()

            # Test toggling aux3
            controller.toggle_aux_equipment(3)

            # Verify packet structure - should set bit 2 for aux3
            call_args = mock_connection.send_packet.call_args[0][0]
            assert len(call_args) == 17  # Command packet length
            assert call_args[:2] == b"\xFF\xAA"  # Sync bytes
            assert call_args[8] == 0x04  # Primary equip byte (bit 2 set for aux3)
            assert call_args[14] == 0x04  # Enable bit 2 for primary equip

    @patch('pycompool.controller.SerialConnection')
    def test_aux_equipment_fails_when_status_unavailable(self, mock_connection_class):
        """Test that aux equipment returns False when current status can't be read."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection

        with patch.object(PoolController, 'get_status') as mock_status:
            # Mock get_status to return None (status unavailable)
            mock_status.return_value = None

            controller = PoolController()

            # Should return False when status can't be read
            result = controller.set_aux_equipment(1, True)

            assert result is False
            # No packet should be sent
            mock_connection.send_packet.assert_not_called()


class TestServiceModeProtection:
    """Test service mode safety checks across all command methods."""

    @patch('pycompool.controller.SerialConnection')
    def test_pool_temperature_blocked_in_service_mode(self, mock_connection_class, capsys):
        """Test pool temperature setting is blocked when service mode is active."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection

        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.return_value = {'service_mode': True}

            controller = PoolController()
            result = controller.set_pool_temperature('80f')

            # Should return False and not send packet
            assert result is False
            mock_connection.send_packet.assert_not_called()

            # Should show warning message
            captured = capsys.readouterr()
            assert "Service mode is active - commands are disabled for safety" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_spa_temperature_blocked_in_service_mode(self, mock_connection_class, capsys):
        """Test spa temperature setting is blocked when service mode is active."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection

        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.return_value = {'service_mode': True}

            controller = PoolController()
            result = controller.set_spa_temperature('104f')

            assert result is False
            mock_connection.send_packet.assert_not_called()

            captured = capsys.readouterr()
            assert "Service mode is active - commands are disabled for safety" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_heater_mode_blocked_in_service_mode(self, mock_connection_class, capsys):
        """Test heater mode setting is blocked when service mode is active."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection

        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.return_value = {'service_mode': True}

            controller = PoolController()
            result = controller.set_heater_mode('heater', 'pool')

            assert result is False
            mock_connection.send_packet.assert_not_called()

            captured = capsys.readouterr()
            assert "Service mode is active - commands are disabled for safety" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_aux_equipment_blocked_in_service_mode(self, mock_connection_class, capsys):
        """Test auxiliary equipment control is blocked when service mode is active."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection

        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.return_value = {'service_mode': True}

            controller = PoolController()
            result = controller.set_aux_equipment(1, True)

            assert result is False
            mock_connection.send_packet.assert_not_called()

            captured = capsys.readouterr()
            assert "Service mode is active - commands are disabled for safety" in captured.out

    @patch('pycompool.controller.SerialConnection')
    def test_commands_allowed_when_service_mode_false(self, mock_connection_class):
        """Test commands work normally when service mode is false."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.return_value = {'service_mode': False}

            controller = PoolController()

            # All commands should work normally
            assert controller.set_pool_temperature('80f') is True
            assert controller.set_spa_temperature('104f') is True
            assert controller.set_heater_mode('heater', 'pool') is True

            # aux command needs additional mocking
            with patch.object(controller, 'get_status') as mock_aux_status:
                mock_aux_status.return_value = {'primary_equip': '0x00', 'service_mode': False}
                assert controller.set_aux_equipment(1, True) is True

            # Should have sent 4 packets
            assert mock_connection.send_packet.call_count == 4

    @patch('pycompool.controller.SerialConnection')
    def test_commands_allowed_when_status_unavailable(self, mock_connection_class):
        """Test commands work when status check fails (fail open behavior)."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.return_value = None  # Status unavailable

            controller = PoolController()
            result = controller.set_pool_temperature('80f')

            # Should allow command when status is unavailable (fail open)
            assert result is True
            mock_connection.send_packet.assert_called_once()

    @patch('pycompool.controller.SerialConnection')
    def test_commands_allowed_when_status_exception(self, mock_connection_class):
        """Test commands work when status check raises exception."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.send_packet.return_value = True

        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.side_effect = Exception("Connection error")

            controller = PoolController()
            result = controller.set_pool_temperature('80f')

            # Should allow command when status check fails (fail open)
            assert result is True
            mock_connection.send_packet.assert_called_once()

    @patch('pycompool.controller.SerialConnection')
    def test_service_mode_check_uses_short_timeout(self, mock_connection_class):
        """Test that service mode check uses a short timeout."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection

        with patch.object(PoolController, 'get_status') as mock_status:
            mock_status.return_value = {'service_mode': False}

            controller = PoolController()
            controller.set_pool_temperature('80f')

            # Should call get_status with 2.0 second timeout for service mode check
            # and then again during normal operation
            assert mock_status.call_count >= 1
            # First call should be with 2.0 timeout for service mode check
            first_call = mock_status.call_args_list[0]
            assert first_call[1]['timeout'] == 2.0
