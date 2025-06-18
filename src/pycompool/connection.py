"""
Serial connection management for Compool controllers.

This module handles RS-485 serial connections including USB adapters
and network-based serial connections.
"""

import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Optional

import serial
from serial import serial_for_url
from serial.rs485 import RS485Settings

from .protocol import (
    ACK_OPCODE,
    ACK_PREFIX,
    ACK_TYPE_OK,
    BAUD_DEFAULT,
    SYNC,
)


class ConnectionError(Exception):
    """Raised when connection operations fail."""


class SerialConnection:
    """Manages serial connection to pool controller."""

    def __init__(self, port: Optional[str] = None, baud: Optional[int] = None):
        """
        Initialize connection parameters.

        Args:
            port: Serial port or URL (defaults to COMPOOL_PORT env var)
            baud: Baud rate (defaults to COMPOOL_BAUD env var)
        """
        self.port = port if port is not None else os.getenv("COMPOOL_PORT", "/dev/ttyUSB0")
        self.baud = baud or int(os.getenv("COMPOOL_BAUD", str(BAUD_DEFAULT)))

    @contextmanager
    def open(self) -> Generator[serial.Serial, None, None]:
        """
        Context manager for opening serial connection.

        Yields:
            Serial connection object

        Raises:
            ConnectionError: If connection fails
        """
        try:
            conn = self._create_connection()
            yield conn
        except Exception as e:
            raise ConnectionError(f"Failed to open {self.port}: {e}") from e
        finally:
            if 'conn' in locals():
                conn.close()

    def _create_connection(self) -> serial.Serial:
        """Create and configure serial connection."""
        is_socket = self.port.startswith(("socket://", "rfc2217://"))

        kwargs = {
            'baudrate': self.baud,
            'bytesize': 8,
            'parity': 'N',
            'stopbits': 1,
            'timeout': 0.3
        }

        # Add RS485 settings for non-network connections
        if not is_socket:
            kwargs["rs485_mode"] = RS485Settings(
                rts_level_for_tx=True,
                rts_level_for_rx=False
            )

        return serial_for_url(self.port, **kwargs)

    def send_packet(self, packet_data: bytes, ack_timeout: float = 2.0) -> bool:
        """
        Send a packet and wait for ACK response.

        Args:
            packet_data: Raw packet bytes to send
            ack_timeout: Timeout in seconds to wait for ACK

        Returns:
            True if ACK received, False otherwise

        Raises:
            ConnectionError: If send operation fails
        """
        try:
            with self.open() as conn:
                conn.write(packet_data)
                return self._wait_for_ack(conn, ack_timeout)
        except Exception as e:
            raise ConnectionError(f"Failed to send packet: {e}") from e

    def _wait_for_ack(self, conn: serial.Serial, timeout: float) -> bool:
        """Wait for ACK packet response."""
        deadline = time.time() + timeout
        buf = bytearray()

        while time.time() < deadline:
            chunk = conn.read(32)
            if chunk:
                buf.extend(chunk)

                # Look for ACK prefix
                idx = buf.find(ACK_PREFIX)
                if idx != -1 and len(buf) - idx >= 9:
                    # Parse ACK packet
                    _, _, _, _, op, _, acked, *_ = buf[idx:idx+9]
                    return op == ACK_OPCODE and acked == ACK_TYPE_OK

        return False

    def read_packets(self, packet_size: int = 24, timeout: float = 1.0) -> Generator[bytes, None, None]:
        """
        Generator that yields packets as they are received.

        Args:
            packet_size: Expected packet size in bytes
            timeout: Read timeout per operation

        Yields:
            Raw packet bytes

        Raises:
            ConnectionError: If connection fails
        """
        try:
            with self.open() as conn:
                conn.timeout = timeout
                buf = bytearray()

                while True:
                    chunk = conn.read(24)
                    if chunk:
                        buf.extend(chunk)

                        # Look for complete packets
                        while True:
                            sync_idx = buf.find(SYNC)
                            if sync_idx == -1:
                                break

                            # Remove data before sync
                            if sync_idx > 0:
                                buf = buf[sync_idx:]

                            # Check if we have a complete packet
                            if len(buf) < packet_size:
                                break

                            # Extract and yield packet
                            packet_data = bytes(buf[:packet_size])
                            yield packet_data

                            # Remove processed packet
                            buf = buf[packet_size:]
                    else:
                        # No more data, exit generator
                        break

                    # Prevent buffer overflow
                    if len(buf) > 1000:
                        buf = buf[-100:]

        except Exception as e:
            raise ConnectionError(f"Failed to read packets: {e}") from e
