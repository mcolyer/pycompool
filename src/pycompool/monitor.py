"""
Real-time monitoring of pool controller heartbeat packets.

This module provides functionality to monitor and display real-time
status from pool controllers via heartbeat packets.
"""

import signal
import sys
import time
from typing import Any, Optional

from .connection import ConnectionError, SerialConnection
from .protocol import parse_heartbeat_packet


class PoolMonitor:
    """
    Monitor for pool controller heartbeat packets.

    Listens for heartbeat packets sent every ~2.5 seconds by the controller
    and displays real-time system status.
    """

    def __init__(self, port: Optional[str] = None, baud: Optional[int] = None):
        """
        Initialize monitor.

        Args:
            port: Serial port or URL (defaults to COMPOOL_PORT env var)
            baud: Baud rate (defaults to COMPOOL_BAUD env var)
        """
        self.connection = SerialConnection(port, baud)
        self._stop_monitoring = False

    def start(self, verbose: bool = False) -> None:
        """
        Start monitoring heartbeat packets.

        Args:
            verbose: Enable verbose debug output

        Monitors until Ctrl-C is pressed or an error occurs.
        """
        # Set up signal handler for graceful exit
        def signal_handler(signum: int, frame: Any) -> None:
            print("\n\nStopping monitor...")
            self._stop_monitoring = True

        signal.signal(signal.SIGINT, signal_handler)

        print(f"Monitoring {self.connection.port} at {self.connection.baud} "
              f"baud for heartbeat packets...")
        print("Press Ctrl-C to exit\n")

        try:
            self._monitor_loop(verbose)
        except ConnectionError as e:
            if not self._stop_monitoring:
                sys.exit(f"Connection error: {e}")
        except Exception as e:
            if not self._stop_monitoring:
                sys.exit(f"Unexpected error: {e}")

        print("Monitor stopped.")

    def _monitor_loop(self, verbose: bool) -> None:
        """Main monitoring loop."""
        last_activity = time.time()

        for packet_data in self.connection.read_packets(packet_size=24, timeout=30.0):
            if self._stop_monitoring:
                break

            if verbose:
                print(f"Received {len(packet_data)} bytes: {packet_data.hex(' ')}")

            last_activity = time.time()
            parsed = parse_heartbeat_packet(packet_data)

            if parsed:
                self._display_heartbeat(parsed, verbose)
            elif verbose:
                print(f"Failed to parse heartbeat packet: {packet_data.hex(' ')}")

            # Show periodic status if no recent packets
            now = time.time()
            if now - last_activity > 10:  # 10 seconds without data
                print(f"[{time.strftime('%H:%M:%S')}] Waiting for packets...")
                last_activity = now

    def _display_heartbeat(self, parsed: dict, verbose: bool) -> None:
        """Display parsed heartbeat packet information."""
        timestamp = time.strftime("%H:%M:%S")

        # Build status flags
        status_flags = []
        if parsed['service_mode']:
            status_flags.append("SERVICE")
        if parsed['heater_on']:
            status_flags.append("HEAT")
        if parsed['solar_on']:
            status_flags.append("SOLAR")
        if parsed['freeze_mode']:
            status_flags.append("FREEZE")

        # Add auxiliary equipment status
        aux_flags = []
        for i in range(1, 9):  # aux1-aux8
            if parsed.get(f'aux{i}_on', False):
                aux_flags.append(f"AUX{i}")

        if aux_flags:
            status_flags.extend(aux_flags)

        status = f" [{'/'.join(status_flags)}]" if status_flags else ""

        # Main status line
        print(f"[{timestamp}] "
              f"Pool: {parsed['pool_water_temp_f']:.1f}°F/{parsed['desired_pool_temp_f']:.1f}°F  "
              f"Spa: {parsed['spa_water_temp_f']:.1f}°F/{parsed['desired_spa_temp_f']:.1f}°F  "
              f"Air: {parsed['air_temp_f']:.1f}°F  "
              f"Time: {parsed['time']}{status}")

        # Verbose details
        if verbose:
            print(f"          Version: {parsed['version']} "
                  f"Primary: {parsed['primary_equip']} "
                  f"Secondary: {parsed['secondary_equip']}")
            print(f"          Pool Solar: {parsed['pool_solar_temp']:.1f}°C "
                  f"Spa Solar: {parsed['spa_solar_temp']:.1f}°C")

            # Show auxiliary equipment states
            aux_states = []
            for i in range(1, 9):  # aux1-aux8
                state = "ON" if parsed.get(f'aux{i}_on', False) else "OFF"
                aux_states.append(f"AUX{i}:{state}")

            print(f"          Equipment: {' '.join(aux_states)}")


def monitor_command(
    port: Optional[str] = None,
    baud: Optional[int] = None,
    verbose: bool = False
) -> None:
    """
    Command function for monitoring heartbeat packets.

    Args:
        port: Serial port override
        baud: Baud rate override
        verbose: Enable verbose debug output
    """
    monitor = PoolMonitor(port, baud)
    monitor.start(verbose)
