"""
Protocol constants and packet parsing functions for Compool LX3xxx controllers.

This module contains the RS-485 protocol implementation including packet
structures, checksums, and temperature conversions.
"""

import re
import struct
from enum import Enum
from typing import Optional


class ProtocolError(Exception):
    """Raised when protocol operations fail."""


class PacketType(Enum):
    """Types of packets in the Compool protocol."""
    COMMAND = "command"
    HEARTBEAT = "heartbeat"
    ACK = "ack"
    NACK = "nack"


# ─────────────────── RS-485 / protocol constants ─────────────────────────
SYNC = b"\xFF\xAA"
DEST, SRC = 0x00, 0x01
OPCODE = 0x82
INFO_LEN = 0x09
ACK_PREFIX = b"\xFF\xAA\x01"
ACK_OPCODE = 0x01
ACK_TYPE_OK = 0x82
BAUD_DEFAULT = 9600

# Heartbeat/acknowledge packet constants
HEARTBEAT_DEST = 0x0F
HEARTBEAT_OPCODE = 0x02
HEARTBEAT_LEN = 0x10  # 16 bytes of data + header = 24 bytes total


def tempstr_to_celsius(temp_str: str) -> float:
    """
    Convert a temperature string like '80f' or '26.7c' to celsius.

    Args:
        temp_str: Temperature string ending in 'f' or 'c'

    Returns:
        Temperature in celsius

    Raises:
        ValueError: If format is invalid
    """
    match = re.fullmatch(r"(?i)\s*([0-9]+(?:\.[0-9]*)?)\s*([fc])\s*", temp_str)
    if not match:
        raise ValueError("temperature must look like 90f or 25c")

    value, unit = float(match.group(1)), match.group(2).lower()
    return (value - 32) * 5 / 9 if unit == 'f' else value


def celsius_to_byte(temp_celsius: float) -> int:
    """
    Convert celsius temperature to protocol byte encoding.

    Temperature is encoded as 0.25°C increments (temp * 4).

    Args:
        temp_celsius: Temperature in celsius

    Returns:
        Encoded temperature byte (0-255)
    """
    return max(0, min(255, int(round(temp_celsius * 4))))


def byte_to_celsius(temp_byte: int) -> float:
    """
    Convert protocol byte encoding to celsius temperature.

    Args:
        temp_byte: Encoded temperature byte

    Returns:
        Temperature in celsius
    """
    return temp_byte / 4.0


def celsius_to_fahrenheit(temp_celsius: float) -> float:
    """Convert celsius to fahrenheit."""
    return temp_celsius * 9/5 + 32


def calculate_checksum(data: bytes) -> int:
    """
    Calculate 16-bit checksum for packet data.

    Args:
        data: Packet bytes (excluding checksum)

    Returns:
        16-bit checksum
    """
    return sum(data) & 0xFFFF


def parse_heartbeat_packet(data: bytes) -> Optional[dict]:
    """
    Parse a heartbeat/acknowledge packet from the pool controller.

    Args:
        data: Raw packet bytes (24 bytes)

    Returns:
        Parsed packet data dict, or None if invalid
    """
    if len(data) < 24:
        return None

    if data[:2] != SYNC:
        return None

    # Check if this is a heartbeat packet
    dest, version, opcode, info_len = struct.unpack('BBBB', data[2:6])
    if dest != HEARTBEAT_DEST or opcode != HEARTBEAT_OPCODE:
        return None

    # Verify checksum
    payload = data[:-2]
    expected_csum = calculate_checksum(payload)
    actual_csum = (data[-2] << 8) | data[-1]

    if expected_csum != actual_csum:
        return None

    # Parse heartbeat packet fields (24 bytes total)
    minutes, hours = data[6], data[7]
    primary_equip = data[8]
    secondary_equip = data[9]
    delay_heat_source = data[10]  # Delay/Heat source byte
    water_temp = data[11]  # Pool water temp in 0.25°C
    solar_temp = data[12]  # Pool solar temp in 0.5°C
    spa_water_temp = data[13]  # Spa water temp in 0.25°C (3830 only)
    spa_solar_temp = data[14]  # Spa solar temp in 0.5°C (3830 only)
    desired_pool_temp = data[15]  # Desired pool temp in 0.25°C
    desired_spa_temp = data[16]  # Desired spa temp in 0.25°C
    air_temp = data[17]  # Air temp in 0.5°C
    data[20]
    data[21]

    return {
        'type': PacketType.HEARTBEAT,
        'version': version,
        'time': f'{hours:02d}:{minutes:02d}',
        'primary_equip': f'0x{primary_equip:02x}',
        'secondary_equip': f'0x{secondary_equip:02x}',
        'service_mode': bool(secondary_equip & 0x01),
        'heater_on': bool(secondary_equip & 0x02),
        'solar_on': bool(secondary_equip & 0x04),
        'remotes_enabled': bool(secondary_equip & 0x08),
        'freeze_mode': bool(secondary_equip & 0x80),
        # Heat source settings (bits 4-7 of delay_heat_source byte)
        'pool_heat_source': (delay_heat_source >> 4) & 0x03,  # Bits 4-5
        'spa_heat_source': (delay_heat_source >> 6) & 0x03,   # Bits 6-7
        'delay_heat_source_byte': delay_heat_source,  # Raw byte for debugging
        # Primary equipment state (auxiliary circuits - 3820 system layout)
        'aux1_on': bool(primary_equip & 0x01),     # Bit 0
        'aux2_on': bool(primary_equip & 0x02),     # Bit 1
        'aux3_on': bool(primary_equip & 0x04),     # Bit 2
        'aux4_on': bool(primary_equip & 0x08),     # Bit 3
        'aux5_on': bool(primary_equip & 0x10),     # Bit 4
        'aux6_on': bool(primary_equip & 0x20),     # Bit 5
        'aux7_on': bool(primary_equip & 0x40),     # Bit 6
        'aux8_on': bool(primary_equip & 0x80),     # Bit 7
        'pool_water_temp': byte_to_celsius(water_temp) if water_temp else 0,
        'pool_solar_temp': solar_temp / 2.0 if solar_temp else 0,
        'spa_water_temp': byte_to_celsius(spa_water_temp) if spa_water_temp else 0,
        'spa_solar_temp': spa_solar_temp / 2.0 if spa_solar_temp else 0,
        'desired_pool_temp': byte_to_celsius(desired_pool_temp) if desired_pool_temp else 0,
        'desired_spa_temp': byte_to_celsius(desired_spa_temp) if desired_spa_temp else 0,
        'air_temp': air_temp / 2.0 if air_temp else 0,
        'pool_water_temp_f': celsius_to_fahrenheit(byte_to_celsius(water_temp)) if water_temp else 0,
        'spa_water_temp_f': celsius_to_fahrenheit(byte_to_celsius(spa_water_temp)) if spa_water_temp else 0,
        'desired_pool_temp_f': celsius_to_fahrenheit(byte_to_celsius(desired_pool_temp)) if desired_pool_temp else 0,
        'desired_spa_temp_f': celsius_to_fahrenheit(byte_to_celsius(desired_spa_temp)) if desired_spa_temp else 0,
        'air_temp_f': celsius_to_fahrenheit(air_temp / 2.0) if air_temp else 0,
    }


def create_command_packet(pool_temp: int = 0, spa_temp: int = 0, heat_source: int = 0, primary_equip: int = 0, enable_bits: int = 0) -> bytes:
    """
    Create a command packet to send to the controller.

    Args:
        pool_temp: Pool temperature in encoded byte format
        spa_temp: Spa temperature in encoded byte format
        heat_source: Heat source configuration byte
        primary_equip: Primary equipment state byte (auxiliary circuits)
        enable_bits: Bits indicating which fields are valid

    Returns:
        17-byte command packet
    """
    header = [
        *SYNC, DEST, SRC, OPCODE, INFO_LEN,
        0x00, 0x00,          # minutes, hours
        primary_equip, 0x00, heat_source,  # primary, secondary, heat-source
        pool_temp,
        spa_temp,
        0x00,                # switch state
        enable_bits,
    ]
    checksum = calculate_checksum(bytes(header))
    header += [(checksum >> 8) & 0xFF, checksum & 0xFF]
    return bytes(header)
