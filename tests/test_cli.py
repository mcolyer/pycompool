"""Tests for CLI module."""

from unittest.mock import patch

from pycompool.cli import CLI, main


class TestCLI:
    """Test CLI class."""

    @patch('pycompool.cli.set_pool_command')
    def test_set_pool_defaults(self, mock_command):
        """Test set_pool with default parameters."""
        cli = CLI()
        cli.set_pool("80f")

        mock_command.assert_called_once_with("80f", None, None, False)

    @patch('pycompool.cli.set_pool_command')
    def test_set_pool_with_options(self, mock_command):
        """Test set_pool with all options."""
        cli = CLI()
        cli.set_pool("80f", port="/dev/ttyUSB1", baud=19200, verbose=True)

        mock_command.assert_called_once_with("80f", "/dev/ttyUSB1", 19200, True)

    @patch('pycompool.cli.set_spa_command')
    def test_set_spa_defaults(self, mock_command):
        """Test set_spa with default parameters."""
        cli = CLI()
        cli.set_spa("104f")

        mock_command.assert_called_once_with("104f", None, None, False)

    @patch('pycompool.cli.set_spa_command')
    def test_set_spa_with_options(self, mock_command):
        """Test set_spa with all options."""
        cli = CLI()
        cli.set_spa("104f", port="socket://192.168.1.50:8899", baud=9600, verbose=True)

        mock_command.assert_called_once_with("104f", "socket://192.168.1.50:8899", 9600, True)

    @patch('pycompool.cli.monitor_command')
    def test_monitor_defaults(self, mock_command):
        """Test monitor with default parameters."""
        cli = CLI()
        cli.monitor()

        mock_command.assert_called_once_with(None, None, False)

    @patch('pycompool.cli.monitor_command')
    def test_monitor_with_options(self, mock_command):
        """Test monitor with all options."""
        cli = CLI()
        cli.monitor(port="/dev/ttyUSB1", baud=19200, verbose=True)

        mock_command.assert_called_once_with("/dev/ttyUSB1", 19200, True)


class TestMainFunction:
    """Test main function."""

    @patch('pycompool.cli.fire.Fire')
    def test_main(self, mock_fire):
        """Test main function calls Fire with CLI class."""
        main()

        mock_fire.assert_called_once_with(CLI)
