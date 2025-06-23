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


def set_heater_command(
    mode: str,
    target: str,
    port: Optional[str] = None,
    baud: Optional[int] = None,
    verbose: bool = False
) -> bool:
    """
    Command function for setting heater/solar mode.

    Args:
        mode: Heating mode ('off', 'heater', 'solar-priority', 'solar-only')
        target: Target system ('pool' or 'spa')
        port: Serial port override
        baud: Baud rate override
        verbose: Enable verbose output

    Returns:
        True if successful, False otherwise
    """
    controller = PoolController(port, baud)
    return controller.set_heater_mode(mode, target, verbose)


def set_aux_command(
    aux_name: str,
    state: str,
    port: Optional[str] = None,
    baud: Optional[int] = None,
    verbose: bool = False
) -> bool:
    """
    Command function for setting auxiliary equipment state.

    Args:
        aux_name: Auxiliary circuit name ('aux1', 'aux2', etc.)
        state: Desired state ('on' or 'off')
        port: Serial port override
        baud: Baud rate override
        verbose: Enable verbose output

    Returns:
        True if successful, False otherwise
    """
    # Validate and parse aux name
    if not aux_name.startswith('aux'):
        raise ValueError(f"Invalid aux name '{aux_name}'. Must be aux1, aux2, etc.")

    try:
        aux_num = int(aux_name[3:])
    except ValueError as e:
        raise ValueError(f"Invalid aux name '{aux_name}'. Must be aux1, aux2, etc.") from e

    # Validate state
    state_lower = state.lower()
    if state_lower not in ('on', 'off'):
        raise ValueError(f"Invalid state '{state}'. Must be 'on' or 'off'.")

    state_bool = state_lower == 'on'

    controller = PoolController(port, baud)
    return controller.set_aux_equipment(aux_num, state_bool, verbose)
