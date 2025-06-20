"""Tests for commands module."""

from unittest.mock import Mock, patch

from pycompool.commands import set_heater_command, set_pool_command, set_spa_command


class TestCommands:
    """Test command functions."""

    @patch('pycompool.commands.PoolController')
    def test_set_pool_command_success(self, mock_controller_class):
        """Test successful pool command."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.set_pool_temperature.return_value = True

        result = set_pool_command("80f")

        assert result is True
        mock_controller_class.assert_called_once_with(None, None)
        mock_controller.set_pool_temperature.assert_called_once_with("80f", False)

    @patch('pycompool.commands.PoolController')
    def test_set_pool_command_with_options(self, mock_controller_class):
        """Test pool command with port, baud, and verbose options."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.set_pool_temperature.return_value = True

        result = set_pool_command(
            "80f",
            port="/dev/ttyUSB1",
            baud=19200,
            verbose=True
        )

        assert result is True
        mock_controller_class.assert_called_once_with("/dev/ttyUSB1", 19200)
        mock_controller.set_pool_temperature.assert_called_once_with("80f", True)

    @patch('pycompool.commands.PoolController')
    def test_set_pool_command_failure(self, mock_controller_class):
        """Test pool command failure."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.set_pool_temperature.return_value = False

        result = set_pool_command("80f")

        assert result is False

    @patch('pycompool.commands.PoolController')
    def test_set_spa_command_success(self, mock_controller_class):
        """Test successful spa command."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.set_spa_temperature.return_value = True

        result = set_spa_command("104f")

        assert result is True
        mock_controller_class.assert_called_once_with(None, None)
        mock_controller.set_spa_temperature.assert_called_once_with("104f", False)

    @patch('pycompool.commands.PoolController')
    def test_set_spa_command_with_options(self, mock_controller_class):
        """Test spa command with port, baud, and verbose options."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.set_spa_temperature.return_value = True

        result = set_spa_command(
            "104f",
            port="socket://192.168.1.50:8899",
            baud=9600,
            verbose=True
        )

        assert result is True
        mock_controller_class.assert_called_once_with("socket://192.168.1.50:8899", 9600)
        mock_controller.set_spa_temperature.assert_called_once_with("104f", True)

    @patch('pycompool.commands.PoolController')
    def test_set_spa_command_failure(self, mock_controller_class):
        """Test spa command failure."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.set_spa_temperature.return_value = False

        result = set_spa_command("104f")

        assert result is False

    @patch('pycompool.commands.PoolController')
    def test_set_heater_command_success(self, mock_controller_class):
        """Test successful heater command."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.set_heater_mode.return_value = True

        result = set_heater_command("heater", "pool")

        assert result is True
        mock_controller_class.assert_called_once_with(None, None)
        mock_controller.set_heater_mode.assert_called_once_with("heater", "pool", False)

    @patch('pycompool.commands.PoolController')
    def test_set_heater_command_with_options(self, mock_controller_class):
        """Test heater command with port, baud, and verbose options."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.set_heater_mode.return_value = True

        result = set_heater_command(
            "solar-only",
            "spa",
            port="/dev/ttyUSB1",
            baud=19200,
            verbose=True
        )

        assert result is True
        mock_controller_class.assert_called_once_with("/dev/ttyUSB1", 19200)
        mock_controller.set_heater_mode.assert_called_once_with("solar-only", "spa", True)

    @patch('pycompool.commands.PoolController')
    def test_set_heater_command_failure(self, mock_controller_class):
        """Test heater command failure."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.set_heater_mode.return_value = False

        result = set_heater_command("off", "pool")

        assert result is False

    @patch('pycompool.commands.PoolController')
    def test_set_heater_command_all_modes(self, mock_controller_class):
        """Test all heater modes."""
        mock_controller = Mock()
        mock_controller_class.return_value = mock_controller
        mock_controller.set_heater_mode.return_value = True

        modes = ["off", "heater", "solar-priority", "solar-only"]
        targets = ["pool", "spa"]

        for mode in modes:
            for target in targets:
                result = set_heater_command(mode, target)
                assert result is True
