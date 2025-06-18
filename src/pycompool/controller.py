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

    @property
    def port(self) -> str:
        """Get the configured serial port."""
        return self.connection.port

    @property
    def baud(self) -> int:
        """Get the configured baud rate."""
        return self.connection.baud
