"""Tests for connection module."""

from unittest.mock import Mock, patch

import pytest

from pycompool.connection import ConnectionError, SerialConnection
from pycompool.protocol import SYNC


class TestSerialConnection:
    """Test SerialConnection class."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        with patch.dict('os.environ', {}, clear=True):
            conn = SerialConnection()
            assert conn.port == "/dev/ttyUSB0"
            assert conn.baud == 9600

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict('os.environ', {
            'COMPOOL_PORT': 'socket://192.168.1.50:8899',
            'COMPOOL_BAUD': '19200'
        }):
            conn = SerialConnection()
            assert conn.port == "socket://192.168.1.50:8899"
            assert conn.baud == 19200

    def test_init_with_params(self):
        """Test initialization with explicit parameters."""
        conn = SerialConnection("/dev/ttyUSB1", 38400)
        assert conn.port == "/dev/ttyUSB1"
        assert conn.baud == 38400

    def test_params_override_env(self):
        """Test that explicit params override environment."""
        with patch.dict('os.environ', {
            'COMPOOL_PORT': '/dev/ttyUSB0',
            'COMPOOL_BAUD': '9600'
        }):
            conn = SerialConnection("/dev/ttyUSB1", 19200)
            assert conn.port == "/dev/ttyUSB1"
            assert conn.baud == 19200

    @patch('pycompool.connection.serial_for_url')
    def test_create_connection_serial_port(self, mock_serial):
        """Test serial port connection creation."""
        conn = SerialConnection("/dev/ttyUSB0", 9600)
        mock_ser = Mock()
        mock_serial.return_value = mock_ser

        result = conn._create_connection()

        mock_serial.assert_called_once()
        call_args = mock_serial.call_args
        assert call_args[0][0] == "/dev/ttyUSB0"
        assert call_args[1]['baudrate'] == 9600
        assert call_args[1]['bytesize'] == 8
        assert call_args[1]['parity'] == 'N'
        assert call_args[1]['stopbits'] == 1
        assert 'rs485_mode' in call_args[1]
        assert result == mock_ser

    @patch('pycompool.connection.serial_for_url')
    def test_create_connection_socket(self, mock_serial):
        """Test socket connection creation."""
        conn = SerialConnection("socket://192.168.1.50:8899", 9600)
        mock_ser = Mock()
        mock_serial.return_value = mock_ser

        result = conn._create_connection()

        mock_serial.assert_called_once()
        call_args = mock_serial.call_args
        assert call_args[0][0] == "socket://192.168.1.50:8899"
        assert 'rs485_mode' not in call_args[1]  # No RS485 for socket
        assert result == mock_ser

    @patch('pycompool.connection.serial_for_url')
    def test_open_context_manager(self, mock_serial):
        """Test open context manager."""
        conn = SerialConnection("/dev/ttyUSB0")
        mock_ser = Mock()
        mock_serial.return_value = mock_ser

        with conn.open() as ser:
            assert ser == mock_ser

        mock_ser.close.assert_called_once()

    @patch('pycompool.connection.serial_for_url')
    def test_open_context_manager_exception(self, mock_serial):
        """Test open context manager with exception."""
        conn = SerialConnection("/dev/ttyUSB0")
        mock_serial.side_effect = Exception("Connection failed")

        with pytest.raises(ConnectionError, match="Failed to open"):
            with conn.open():
                pass

    @patch('pycompool.connection.serial_for_url')
    def test_send_packet_success(self, mock_serial):
        """Test successful packet send with ACK."""
        conn = SerialConnection("/dev/ttyUSB0")
        mock_ser = Mock()
        mock_serial.return_value = mock_ser

        # Mock ACK response
        ack_packet = b"\xFF\xAA\x01\x10\x01\x01\x82\x00\x00"
        mock_ser.read.return_value = ack_packet

        packet_data = b"\xFF\xAA\x00\x01\x82\x09" + b"\x00" * 11
        result = conn.send_packet(packet_data)

        assert result is True
        mock_ser.write.assert_called_once_with(packet_data)

    @patch('pycompool.connection.serial_for_url')
    def test_send_packet_no_ack(self, mock_serial):
        """Test packet send with no ACK response."""
        conn = SerialConnection("/dev/ttyUSB0")
        mock_ser = Mock()
        mock_serial.return_value = mock_ser

        # No response
        mock_ser.read.return_value = b""

        packet_data = b"\xFF\xAA\x00\x01\x82\x09" + b"\x00" * 11
        result = conn.send_packet(packet_data, ack_timeout=0.1)

        assert result is False

    @patch('pycompool.connection.serial_for_url')
    def test_send_packet_connection_error(self, mock_serial):
        """Test packet send with connection error."""
        conn = SerialConnection("/dev/ttyUSB0")
        mock_serial.side_effect = Exception("Connection failed")

        packet_data = b"\xFF\xAA\x00\x01\x82\x09" + b"\x00" * 11

        with pytest.raises(ConnectionError, match="Failed to send packet"):
            conn.send_packet(packet_data)

    @patch('pycompool.connection.serial_for_url')
    def test_read_packets_generator(self, mock_serial):
        """Test packet reading generator."""
        conn = SerialConnection("/dev/ttyUSB0")
        mock_ser = Mock()
        mock_serial.return_value = mock_ser

        # Create test packets
        packet1 = SYNC + b"\x0F\x10\x02\x10" + b"\x00" * 18
        packet2 = SYNC + b"\x0F\x11\x02\x10" + b"\x00" * 18

        # Mock reading chunks
        mock_ser.read.side_effect = [
            packet1[:12],  # First chunk
            packet1[12:] + packet2[:8],  # Second chunk with partial next packet
            packet2[8:],  # Rest of second packet
            b"",  # End - triggers break
        ]

        packets = list(conn.read_packets(packet_size=24, timeout=0.1))

        assert len(packets) == 2
        assert packets[0] == packet1
        assert packets[1] == packet2

    @patch('pycompool.connection.serial_for_url')
    def test_read_packets_with_noise(self, mock_serial):
        """Test packet reading with noise before sync."""
        conn = SerialConnection("/dev/ttyUSB0")
        mock_ser = Mock()
        mock_serial.return_value = mock_ser

        # Noise + valid packet
        noise = b"\x12\x34\x56"
        packet = SYNC + b"\x0F\x10\x02\x10" + b"\x00" * 18

        mock_ser.read.side_effect = [
            noise + packet,
            b"",  # End - triggers break
        ]

        packets = list(conn.read_packets(packet_size=24, timeout=0.1))

        assert len(packets) == 1
        assert packets[0] == packet
