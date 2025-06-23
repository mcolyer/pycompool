"""Tests for monitor module."""

from unittest.mock import Mock, patch

from pycompool.monitor import PoolMonitor, monitor_command
from pycompool.protocol import PacketType


class TestPoolMonitor:
    """Test PoolMonitor class."""

    def test_init_defaults(self):
        """Test initialization with defaults."""
        monitor = PoolMonitor()
        assert monitor.connection is not None
        assert monitor._stop_monitoring is False

    def test_init_with_params(self):
        """Test initialization with parameters."""
        monitor = PoolMonitor("/dev/ttyUSB1", 19200)
        assert monitor.connection.port == "/dev/ttyUSB1"
        assert monitor.connection.baud == 19200

    @patch('pycompool.monitor.signal')
    @patch('pycompool.monitor.SerialConnection')
    def test_start_signal_handler(self, mock_connection_class, mock_signal):
        """Test that signal handler is set up."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.read_packets.return_value = []  # Empty iterator

        monitor = PoolMonitor()
        monitor.start()

        # Verify signal handler was registered
        mock_signal.signal.assert_called_once()
        args = mock_signal.signal.call_args[0]
        assert args[0] == mock_signal.SIGINT
        assert callable(args[1])  # Handler function

    @patch('pycompool.monitor.signal')
    @patch('pycompool.monitor.SerialConnection')
    def test_start_calls_monitor_loop(self, mock_connection_class, mock_signal):
        """Test that start calls the monitor loop."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection
        mock_connection.read_packets.return_value = []  # Empty iterator

        monitor = PoolMonitor()
        monitor.start()

        # Verify read_packets was called with extended timeout
        mock_connection.read_packets.assert_called_once_with(packet_size=24, timeout=30.0)

    def create_test_heartbeat_data(self):
        """Create test heartbeat packet data."""
        return {
            'type': PacketType.HEARTBEAT,
            'version': 16,
            'time': '14:30',
            'pool_water_temp_f': 75.0,
            'desired_pool_temp_f': 80.0,
            'spa_water_temp_f': 102.0,
            'desired_spa_temp_f': 104.0,
            'air_temp_f': 70.0,
            'service_mode': False,
            'heater_on': True,
            'solar_on': False,
            'freeze_mode': False,
            'primary_equip': '0x03',
            'secondary_equip': '0x02',
            'pool_solar_temp': 35.0,
            'spa_solar_temp': 45.0,
            # Auxiliary equipment states (3820 system layout)
            'aux1_on': True,   # bit 0 of 0x03
            'aux2_on': True,   # bit 1 of 0x03
            'aux3_on': False,
            'aux4_on': False,
            'aux5_on': False,
            'aux6_on': False,
            'aux7_on': False,
            'aux8_on': False,
        }

    def test_display_heartbeat_basic(self, capsys):
        """Test basic heartbeat display."""
        monitor = PoolMonitor()
        heartbeat_data = self.create_test_heartbeat_data()

        with patch('pycompool.monitor.time.strftime', return_value='14:30:15'):
            monitor._display_heartbeat(heartbeat_data, verbose=False)

        captured = capsys.readouterr()
        assert "[14:30:15]" in captured.out
        assert "Pool: 75.0°F/80.0°F" in captured.out
        assert "Spa: 102.0°F/104.0°F" in captured.out
        assert "Air: 70.0°F" in captured.out
        assert "Time: 14:30" in captured.out
        assert "[HEAT/AUX1/AUX2]" in captured.out  # Status flags including aux equipment

    def test_display_heartbeat_verbose(self, capsys):
        """Test verbose heartbeat display."""
        monitor = PoolMonitor()
        heartbeat_data = self.create_test_heartbeat_data()

        with patch('pycompool.monitor.time.strftime', return_value='14:30:15'):
            monitor._display_heartbeat(heartbeat_data, verbose=True)

        captured = capsys.readouterr()
        assert "Version: 16" in captured.out
        assert "Primary: 0x03" in captured.out
        assert "Secondary: 0x02" in captured.out
        assert "Pool Solar: 35.0°C" in captured.out
        assert "Spa Solar: 45.0°C" in captured.out

    def test_display_heartbeat_multiple_flags(self, capsys):
        """Test heartbeat display with multiple status flags."""
        monitor = PoolMonitor()
        heartbeat_data = self.create_test_heartbeat_data()
        heartbeat_data.update({
            'service_mode': True,
            'solar_on': True,
            'freeze_mode': True,
        })

        with patch('pycompool.monitor.time.strftime', return_value='14:30:15'):
            monitor._display_heartbeat(heartbeat_data, verbose=False)

        captured = capsys.readouterr()
        assert "[SERVICE/HEAT/SOLAR/FREEZE/AUX1/AUX2]" in captured.out

    def test_display_heartbeat_no_flags(self, capsys):
        """Test heartbeat display with no status flags."""
        monitor = PoolMonitor()
        heartbeat_data = self.create_test_heartbeat_data()
        heartbeat_data.update({
            'service_mode': False,
            'heater_on': False,
            'solar_on': False,
            'freeze_mode': False,
            'aux1_on': False,
            'aux2_on': False,
            'aux3_on': False,
            'aux4_on': False,
            'aux5_on': False,
            'aux6_on': False,
            'aux7_on': False,
            'aux8_on': False,
        })

        with patch('pycompool.monitor.time.strftime', return_value='14:30:15'):
            monitor._display_heartbeat(heartbeat_data, verbose=False)

        captured = capsys.readouterr()
        # Should not have status flags section
        assert "] [" not in captured.out
        assert "Time: 14:30" in captured.out  # No flags after time
        assert not captured.out.strip().endswith("]")  # No trailing flags

    @patch('pycompool.monitor.parse_heartbeat_packet')
    @patch('pycompool.monitor.SerialConnection')
    @patch('pycompool.monitor.signal')
    def test_monitor_loop_packet_processing(self, mock_signal, mock_connection_class, mock_parse, capsys):
        """Test monitor loop packet processing."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection

        # Mock packet data
        packet_data = b"\xFF\xAA" + b"\x00" * 22
        mock_connection.read_packets.return_value = [packet_data]

        # Mock successful parsing
        heartbeat_data = self.create_test_heartbeat_data()
        mock_parse.return_value = heartbeat_data

        monitor = PoolMonitor()

        # Mock time to avoid actual waiting
        with patch('pycompool.monitor.time.time', side_effect=[0, 1, 2, 15]):  # Trigger timeout
            with patch('pycompool.monitor.time.strftime', return_value='14:30:15'):
                monitor._monitor_loop(verbose=False)

        # Verify parsing was called
        mock_parse.assert_called_once_with(packet_data)

        # Verify output
        captured = capsys.readouterr()
        assert "Pool: 75.0°F/80.0°F" in captured.out

    @patch('pycompool.monitor.parse_heartbeat_packet')
    @patch('pycompool.monitor.SerialConnection')
    @patch('pycompool.monitor.signal')
    def test_monitor_loop_parse_failure_verbose(self, mock_signal, mock_connection_class, mock_parse, capsys):
        """Test monitor loop with parse failure in verbose mode."""
        mock_connection = Mock()
        mock_connection_class.return_value = mock_connection

        # Mock packet data
        packet_data = b"\xFF\xAA" + b"\x00" * 22
        mock_connection.read_packets.return_value = [packet_data]

        # Mock failed parsing
        mock_parse.return_value = None

        monitor = PoolMonitor()

        # Mock time to avoid actual waiting
        with patch('pycompool.monitor.time.time', side_effect=[0, 1, 2, 15]):  # Trigger timeout
            monitor._monitor_loop(verbose=True)

        # Verify output shows parse failure
        captured = capsys.readouterr()
        assert "Failed to parse heartbeat packet:" in captured.out


class TestMonitorCommand:
    """Test monitor_command function."""

    @patch('pycompool.monitor.PoolMonitor')
    def test_monitor_command_defaults(self, mock_monitor_class):
        """Test monitor command with defaults."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor

        monitor_command()

        mock_monitor_class.assert_called_once_with(None, None)
        mock_monitor.start.assert_called_once_with(False)

    @patch('pycompool.monitor.PoolMonitor')
    def test_monitor_command_with_options(self, mock_monitor_class):
        """Test monitor command with options."""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor

        monitor_command(
            port="/dev/ttyUSB1",
            baud=19200,
            verbose=True
        )

        mock_monitor_class.assert_called_once_with("/dev/ttyUSB1", 19200)
        mock_monitor.start.assert_called_once_with(True)
