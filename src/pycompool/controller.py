"""
Main pool controller class providing high-level API.

This module provides the PoolController class which is the main interface
for interacting with Compool LX3xxx controllers.
"""

from typing import Optional

from .connection import SerialConnection
from .protocol import (
    celsius_to_byte,
    celsius_to_fahrenheit,
    create_command_packet,
    parse_heartbeat_packet,
    tempstr_to_celsius,
)


class PoolController:
    """
    High-level interface for controlling Compool LX3xxx pool systems.

    This class provides methods for setting temperatures and retrieving
    system status from pool controllers.
    """

    def __init__(self, port: Optional[str] = None, baud: Optional[int] = None):
        """
        Initialize pool controller interface.

        Args:
            port: Serial port or URL (defaults to COMPOOL_PORT env var)
            baud: Baud rate (defaults to COMPOOL_BAUD env var)
        """
        self.connection = SerialConnection(port, baud)

    def _check_service_mode(self) -> bool:
        """
        Check if the system is in service mode before sending commands.

        Returns:
            True if service mode is active (commands should be blocked), False otherwise
        """
        try:
            status = self.get_status(timeout=2.0)
            if status and status.get('service_mode', False):
                print("⚠️  Service mode is active - commands are disabled for safety")
                return True
        except Exception:
            # If we can't get status, allow the command (fail open)
            pass
        return False

    def set_pool_temperature(self, temperature: str, verbose: bool = False) -> bool:
        """
        Set the desired pool temperature.

        Args:
            temperature: Temperature string like '80f' or '26.7c'
            verbose: Enable verbose output

        Returns:
            True if command was acknowledged, False otherwise

        Example:
            >>> controller = PoolController()
            >>> controller.set_pool_temperature('80f')
            True
        """
        # Check if system is in service mode
        if self._check_service_mode():
            return False

        temp_celsius = tempstr_to_celsius(temperature)
        temp_byte = celsius_to_byte(temp_celsius)
        enable_bits = 1 << 5  # Enable pool temperature field

        packet = create_command_packet(
            pool_temp=temp_byte,
            enable_bits=enable_bits
        )

        if verbose:
            print(f"→ {packet.hex(' ')}")

        success = self.connection.send_packet(packet)
        temp_fahrenheit = celsius_to_fahrenheit(temp_celsius)

        print(f"Pool set-point → {temp_fahrenheit:.1f} °F — "
              f"{'✓ ACK' if success else '✗ NO ACK'}")

        return success

    def set_spa_temperature(self, temperature: str, verbose: bool = False) -> bool:
        """
        Set the desired spa temperature.

        Args:
            temperature: Temperature string like '104f' or '40c'
            verbose: Enable verbose output

        Returns:
            True if command was acknowledged, False otherwise

        Example:
            >>> controller = PoolController()
            >>> controller.set_spa_temperature('104f')
            True
        """
        # Check if system is in service mode
        if self._check_service_mode():
            return False

        temp_celsius = tempstr_to_celsius(temperature)
        temp_byte = celsius_to_byte(temp_celsius)
        enable_bits = 1 << 6  # Enable spa temperature field

        packet = create_command_packet(
            spa_temp=temp_byte,
            enable_bits=enable_bits
        )

        if verbose:
            print(f"→ {packet.hex(' ')}")

        success = self.connection.send_packet(packet)
        temp_fahrenheit = celsius_to_fahrenheit(temp_celsius)

        print(f"Spa set-point → {temp_fahrenheit:.1f} °F — "
              f"{'✓ ACK' if success else '✗ NO ACK'}")

        return success

    def set_heater_mode(self, mode: str, target: str, verbose: bool = False) -> bool:
        """
        Set the heater/solar mode for pool or spa.

        Args:
            mode: Heating mode ('off', 'heater', 'solar-priority', 'solar-only')
            target: Target system ('pool' or 'spa')
            verbose: Enable verbose output

        Returns:
            True if command was acknowledged, False otherwise

        Example:
            >>> controller = PoolController()
            >>> controller.set_heater_mode('heater', 'pool')
            True
        """
        # Check if system is in service mode
        if self._check_service_mode():
            return False

        # Validate inputs
        valid_modes = {'off', 'heater', 'solar-priority', 'solar-only'}
        valid_targets = {'pool', 'spa'}

        if mode not in valid_modes:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}")
        if target not in valid_targets:
            raise ValueError(f"Invalid target '{target}'. Must be one of: {', '.join(valid_targets)}")

        # Map mode to bits
        mode_bits = {
            'off': 0b00,
            'heater': 0b01,
            'solar-priority': 0b10,
            'solar-only': 0b11
        }

        # Calculate heat source byte
        # Pool uses bits 4-5, Spa uses bits 6-7
        heat_source = 0
        if target == 'pool':
            heat_source = mode_bits[mode] << 4  # Bits 4-5
        else:  # spa
            heat_source = mode_bits[mode] << 6  # Bits 6-7

        enable_bits = 1 << 4  # Enable heat source field (bit 4)

        packet = create_command_packet(
            heat_source=heat_source,
            enable_bits=enable_bits
        )

        if verbose:
            print(f"→ {packet.hex(' ')}")

        success = self.connection.send_packet(packet)

        print(f"{target.capitalize()} heating → {mode} — "
              f"{'✓ ACK' if success else '✗ NO ACK'}")

        return success

    def set_aux_equipment(self, aux_num: int, state: bool, verbose: bool = False) -> bool:
        """
        Set the state of an auxiliary equipment circuit.

        Args:
            aux_num: Auxiliary circuit number (1-8)
            state: True to turn on, False to turn off
            verbose: Enable verbose output

        Returns:
            True if command was acknowledged, False otherwise

        Example:
            >>> controller = PoolController()
            >>> controller.set_aux_equipment(1, True)  # Turn on aux1
            True
            >>> controller.set_aux_equipment(2, False)  # Turn off aux2
            True
        """
        # Check if system is in service mode
        if self._check_service_mode():
            return False

        # Validate aux number
        if not (1 <= aux_num <= 8):
            raise ValueError(f"Invalid aux number '{aux_num}'. Must be 1-8.")

        # Map aux number to bit position
        # aux1 = bit 0, aux2 = bit 1, etc. (3820 system layout)
        bit_position = aux_num - 1

        # Get current status to preserve other equipment states
        current_status = self.get_status(timeout=2.0)
        current_primary_equip = 0

        if current_status:
            # Extract current primary equipment byte from hex string
            primary_hex = current_status.get('primary_equip', '0x00')
            current_primary_equip = int(primary_hex, 16)

        # Set or clear the bit for this aux circuit
        if state:
            primary_equip = current_primary_equip | (1 << bit_position)
        else:
            primary_equip = current_primary_equip & ~(1 << bit_position)

        # Use bit 0 to enable primary equipment field
        enable_bits = 1 << 0

        packet = create_command_packet(
            primary_equip=primary_equip,
            enable_bits=enable_bits
        )

        if verbose:
            print(f"→ {packet.hex(' ')}")

        success = self.connection.send_packet(packet)

        print(f"Aux{aux_num} → {'ON' if state else 'OFF'} — "
              f"{'✓ ACK' if success else '✗ NO ACK'}")

        return success

    def get_status(self, timeout: float = 10.0) -> Optional[dict]:
        """
        Listen for a single heartbeat packet and return the parsed status data.

        Args:
            timeout: Maximum time to wait for a heartbeat packet in seconds

        Returns:
            Dictionary containing parsed heartbeat data, or None if no packet received

        Example:
            >>> controller = PoolController()
            >>> status = controller.get_status()
            >>> if status:
            ...     print(f"Pool temp: {status['pool_water_temp_f']:.1f}°F")
        """
        for packet_data in self.connection.read_packets(packet_size=24, timeout=timeout):
            parsed = parse_heartbeat_packet(packet_data)
            if parsed:
                return parsed

        return None

    @property
    def port(self) -> str:
        """Get the configured serial port."""
        return self.connection.port

    @property
    def baud(self) -> int:
        """Get the configured baud rate."""
        return self.connection.baud
