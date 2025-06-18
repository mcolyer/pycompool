# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python package for controlling Pentair/Compool LX3xxx pool and spa systems via RS-485 serial communication. The project provides a command-line tool `compoolctl` that can set pool and spa temperatures.

## Architecture

- **compoolctl**: Main CLI executable script that uses Fire for command parsing
- **RS-485 Protocol**: Custom binary protocol implementation for Compool communication  
- **Serial Communication**: Uses PySerial with RS485Settings for hardware control

### Key Components

- `Packet` dataclass: Constructs binary protocol packets with temperature and enable bits
- `Session` dataclass: Manages serial connection and ACK handling
- `CLI` class: Fire-based command interface with `set_pool()` and `set_spa()` methods
- Protocol constants and helper functions for temperature conversion

## Development Commands

```bash
# Install dependencies (uses uv package manager)
uv sync

# Run compoolctl directly
./compoolctl set-pool 90f
./compoolctl set-spa 25c

# Or install and run as a package
uv run compoolctl set-pool 90f

# Test with different serial configurations
COMPOOL_PORT=socket://192.168.0.50:8899 ./compoolctl set-pool 90f
```

## Environment Variables

- `COMPOOL_PORT`: Serial device or PySerial URL (default: /dev/ttyUSB0)
- `COMPOOL_BAUD`: Baud rate (default: 9600)

## Protocol Details

The RS-485 protocol uses:
- Sync bytes: 0xFF 0xAA
- 17-byte packets with checksum
- ACK responses with 2-second timeout
- Temperature encoded as celsius * 4 (0-255 range)
- Enable bits control which setpoint is being modified (bit 5 for pool, bit 6 for spa)