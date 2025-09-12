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

        # Get current heat source state to preserve other target's settings
        current_status = self.get_status(timeout=2.0)
        if current_status:
            current_heat_source = current_status.get('delay_heat_source_byte', 0)
        else:
            # If we can't read current state, start with zero (fail open)
            current_heat_source = 0

        # Calculate heat source byte by preserving existing settings
        # Pool uses bits 4-5, Spa uses bits 6-7
        if target == 'pool':
            # Clear pool bits (4-5) but preserve spa bits (6-7) and delay bits (0-3)
            heat_source = (current_heat_source & 0b11001111) | (mode_bits[mode] << 4)
        else:  # spa
            # Clear spa bits (6-7) but preserve pool bits (4-5) and delay bits (0-3)
            heat_source = (current_heat_source & 0b00111111) | (mode_bits[mode] << 6)

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

        The hardware only supports toggling, so this method reads the current state
        and only sends a toggle command if the current state differs from desired state.

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

        # Get current status to check if toggle is needed
        current_status = self.get_status(timeout=2.0)
        if not current_status:
            return False

        # Check current aux state from heartbeat packet
        current_aux_state = current_status.get(f'aux{aux_num}_on', False)

        # Only toggle if current state differs from desired state
        if current_aux_state == state:
            print(f"Aux{aux_num} already {'ON' if state else 'OFF'} — no action needed")
            return True

        # Send toggle command - only set the bit for this specific aux circuit
        # The hardware interprets set bits as "toggle this circuit"
        bit_position = aux_num - 1
        primary_equip = 1 << bit_position  # Only the aux bit, not full state

        # Use bit 2 to enable primary equipment field
        enable_bits = 1 << 2

        packet = create_command_packet(
            primary_equip=primary_equip,
            enable_bits=enable_bits
        )

        if verbose:
            print(f"→ {packet.hex(' ')}")

        success = self.connection.send_packet(packet)

        print(f"Aux{aux_num} {current_aux_state and 'ON' or 'OFF'} → {'ON' if state else 'OFF'} — "
              f"{'✓ ACK' if success else '✗ NO ACK'}")

        return success

    def toggle_aux_equipment(self, aux_num: int, verbose: bool = False) -> bool:
        """
        Toggle an auxiliary equipment circuit regardless of current state.

        This method always sends a toggle command, matching the Node.js behavior.
        Use this when you want to toggle without checking current state.

        Args:
            aux_num: Auxiliary circuit number (1-8)
            verbose: Enable verbose output

        Returns:
            True if command was acknowledged, False otherwise

        Example:
            >>> controller = PoolController()
            >>> controller.toggle_aux_equipment(1)  # Toggle aux1
            True
        """
        # Check if system is in service mode
        if self._check_service_mode():
            return False

        # Validate aux number
        if not (1 <= aux_num <= 8):
            raise ValueError(f"Invalid aux number '{aux_num}'. Must be 1-8.")

        # Send toggle command - only set the bit for this specific aux circuit
        bit_position = aux_num - 1
        primary_equip = 1 << bit_position  # Only the aux bit, not full state

        # Use bit 2 to enable primary equipment field
        enable_bits = 1 << 2

        packet = create_command_packet(
            primary_equip=primary_equip,
            enable_bits=enable_bits
        )

        if verbose:
            print(f"→ {packet.hex(' ')}")

        success = self.connection.send_packet(packet)

        print(f"Aux{aux_num} TOGGLE — {'✓ ACK' if success else '✗ NO ACK'}")

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
