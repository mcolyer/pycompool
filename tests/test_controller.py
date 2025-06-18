"""Tests for controller module."""

from unittest.mock import Mock, patch

import pytest

from pycompool.controller import PoolController


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

    def test_properties(self):
        """Test controller properties."""
        controller = PoolController("/dev/ttyUSB1", 19200)
        assert controller.port == "/dev/ttyUSB1"
        assert controller.baud == 19200
