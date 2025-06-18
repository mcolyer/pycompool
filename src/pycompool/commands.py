"""
Temperature control commands for pool and spa systems.

This module provides command implementations for setting pool and spa
temperatures. These are used by both the CLI and library interfaces.
"""

from typing import Optional

from .controller import PoolController


def set_pool_command(
    temperature: str,
    port: Optional[str] = None,
    baud: Optional[int] = None,
    verbose: bool = False
) -> bool:
    """
    Command function for setting pool temperature.

    Args:
        temperature: Temperature string like '80f' or '26.7c'
        port: Serial port override
        baud: Baud rate override
        verbose: Enable verbose output

    Returns:
        True if successful, False otherwise
    """
    controller = PoolController(port, baud)
    return controller.set_pool_temperature(temperature, verbose)


def set_spa_command(
    temperature: str,
    port: Optional[str] = None,
    baud: Optional[int] = None,
    verbose: bool = False
) -> bool:
    """
    Command function for setting spa temperature.

    Args:
        temperature: Temperature string like '104f' or '40c'
        port: Serial port override
        baud: Baud rate override
        verbose: Enable verbose output

    Returns:
        True if successful, False otherwise
    """
    controller = PoolController(port, baud)
    return controller.set_spa_temperature(temperature, verbose)
