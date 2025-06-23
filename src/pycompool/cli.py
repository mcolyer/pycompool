"""
Command-line interface for pycompool using Fire.

This module provides the CLI interface that was previously in the
compoolctl script, now using the restructured library modules.
"""

from typing import Optional

import fire

from .commands import (
    set_aux_command,
    set_heater_command,
    set_pool_command,
    set_spa_command,
)
from .monitor import monitor_command


class CLI:
    """Command-line interface for Compool pool controllers."""

    def set_pool(
        self,
        temp: str,
        port: Optional[str] = None,
        baud: Optional[int] = None,
        verbose: bool = False
    ) -> None:
        """
        Set desired pool temperature.

        Args:
            temp: Temperature string ending in 'f' or 'c' (e.g., '80f', '26.7c')
            port: Serial port override
            baud: Baud rate override
            verbose: Enable verbose output

        Examples:
            compoolctl set-pool 80f
            compoolctl set-pool 26.7c --port /dev/ttyUSB1
        """
        set_pool_command(temp, port, baud, verbose)

    def set_spa(
        self,
        temp: str,
        port: Optional[str] = None,
        baud: Optional[int] = None,
        verbose: bool = False
    ) -> None:
        """
        Set desired spa temperature.

        Args:
            temp: Temperature string ending in 'f' or 'c' (e.g., '104f', '40c')
            port: Serial port override
            baud: Baud rate override
            verbose: Enable verbose output

        Examples:
            compoolctl set-spa 104f
            compoolctl set-spa 40c --verbose
        """
        set_spa_command(temp, port, baud, verbose)

    def set_heater(
        self,
        mode: str,
        target: str,
        port: Optional[str] = None,
        baud: Optional[int] = None,
        verbose: bool = False
    ) -> None:
        """
        Set heater/solar mode for pool or spa.

        Args:
            mode: Heating mode ('off', 'heater', 'solar-priority', 'solar-only')
            target: Target system ('pool' or 'spa')
            port: Serial port override
            baud: Baud rate override
            verbose: Enable verbose output

        Examples:
            compoolctl set-heater heater pool
            compoolctl set-heater solar-only spa
            compoolctl set-heater off pool --verbose
        """
        set_heater_command(mode, target, port, baud, verbose)

    def set_aux(
        self,
        aux_name: str,
        state: str,
        port: Optional[str] = None,
        baud: Optional[int] = None,
        verbose: bool = False
    ) -> None:
        """
        Set auxiliary equipment state.

        Args:
            aux_name: Auxiliary circuit name ('aux1', 'aux2', etc.)
            state: Desired state ('on' or 'off')
            port: Serial port override
            baud: Baud rate override
            verbose: Enable verbose output

        Examples:
            compoolctl set-aux aux1 on
            compoolctl set-aux aux2 off
            compoolctl set-aux aux3 on --verbose
        """
        set_aux_command(aux_name, state, port, baud, verbose)

    def monitor(
        self,
        port: Optional[str] = None,
        baud: Optional[int] = None,
        verbose: bool = False
    ) -> None:
        """
        Monitor heartbeat packets from the pool controller.

        Args:
            port: Serial port override
            baud: Baud rate override
            verbose: Enable verbose debug output

        Press Ctrl-C to exit monitoring.

        Examples:
            compoolctl monitor
            compoolctl monitor --verbose
            compoolctl monitor --port socket://192.168.1.50:8899
        """
        monitor_command(port, baud, verbose)


def main() -> None:
    """Main entry point for the CLI."""
    fire.Fire(CLI)


if __name__ == "__main__":
    main()
