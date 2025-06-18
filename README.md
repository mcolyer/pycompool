# pycompool

Control Pentair/Compool LX3xxx pool and spa systems via RS-485 serial communication.

## Overview

This tool provides a command-line interface to interact with Pentair Compool LX3xxx series pool controllers (3400, 3600, 3800, 3810, 3820, 3830). It can set pool and spa temperatures and monitor real-time system status through RS-485 communication.

## Features

- **Set pool temperature** - Control desired pool water temperature
- **Set spa temperature** - Control desired spa water temperature  
- **Monitor system status** - Real-time monitoring of temperatures, equipment status, and controller time
- **Multiple connection types** - Support for serial ports and network connections
- **Environment configuration** - Configurable via environment variables

## Installation

```bash
# Install for development
uv sync --extra dev

# Install package only
uv sync

# Run CLI
uv run compoolctl --help

# Or install the package
pip install -e .
compoolctl --help
```

## Usage

### Set Pool Temperature

```bash
# Set pool to 80°F
compoolctl set-pool 80f

# Set pool to 26.7°C
compoolctl set-pool 26.7c
```

### Set Spa Temperature

```bash
# Set spa to 104°F
compoolctl set-spa 104f

# Set spa to 40°C
compoolctl set-spa 40c
```

### Monitor System Status

```bash
# Monitor heartbeat packets
compoolctl monitor

# Monitor with verbose debugging
compoolctl monitor --verbose
```

### Library Usage

The package can also be used as a Python library:

```python
from pycompool import PoolController
from pycompool.monitor import PoolMonitor

# Set temperatures
controller = PoolController("/dev/ttyUSB0", 9600)
controller.set_pool_temperature("80f")
controller.set_spa_temperature("104f")

# Monitor heartbeats
monitor = PoolMonitor("/dev/ttyUSB0", 9600)
monitor.start(verbose=True)
```

Monitor output shows:
- Current and desired pool/spa temperatures
- Air temperature
- Controller time
- Status flags (SERVICE/HEAT/SOLAR/FREEZE modes)

Example output:
```
[14:23:15] Pool: 75.2°F/80.0°F  Spa: 98.5°F/104.0°F  Air: 72.1°F  Time: 14:23 [HEAT]
```

## Configuration

### Environment Variables

- `COMPOOL_PORT` - Serial device or PySerial URL (default: `/dev/ttyUSB0`)
- `COMPOOL_BAUD` - Baud rate (default: `9600`)

### Connection Examples

```bash
# USB serial adapter
export COMPOOL_PORT=/dev/ttyUSB0

# Network connection via socket
export COMPOOL_PORT=socket://192.168.0.50:8899

# RFC2217 network serial
export COMPOOL_PORT=rfc2217://pool-controller.local:4001

# Custom baud rate
export COMPOOL_BAUD=19200
```

### Command Line Options

All commands support these options:
- `--port` - Override COMPOOL_PORT
- `--baud` - Override COMPOOL_BAUD  
- `--verbose` - Enable debug output

```bash
compoolctl set-pool 80f --port /dev/ttyUSB1 --baud 19200 --verbose
```

## Hardware Setup

The RS-485 interface uses these settings:
- **Baud Rate**: 9600 bps
- **Data Bits**: 8
- **Stop Bits**: 1
- **Parity**: None
- **Termination**: 1000� resistor

### RJ45 Pinout

| Pin | Function |
|-----|----------|
| 1   | Ground |
| 2   | +10VDC (~100mA max) |
| 3   | +Data (RS485) |
| 4   | -Data (RS485) |
| 5   | +10VDC (~100mA max) |
| 6   | Ground |

## Protocol Details

The system uses a custom RS-485 protocol:

- **Command packets** (17 bytes) - Sent to controller to change settings
- **Heartbeat packets** (24 bytes) - Sent by controller every ~2.5 seconds with status
- **ACK/NACK packets** (9 bytes) - Acknowledgment responses

Temperature encoding:
- Water temperatures: 0.25�C increments
- Solar temperatures: 0.5�C increments  
- Air temperature: 0.5�C increments

## Supported Controllers

- **3400** - Basic pool controller
- **3600** - Pool controller with additional auxiliaries
- **3800** - Pool controller
- **3810** - Dual temperature controller (High/Low instead of Spa/Pool)
- **3820** - 8-circuit controller
- **3830** - Spa and pool controller with separate heating

## Dependencies

- `fire` - Command-line interface framework
- `pyserial` - Serial communication library

## Development

### Setup

```bash
# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/pycompool --cov-report=term-missing

# Run linter
uv run ruff check

# Auto-fix linting issues
uv run ruff check --fix

# Type checking
uv run mypy src/pycompool
```

### Project Structure

```
src/pycompool/
├── __init__.py         # Package exports
├── protocol.py         # Protocol constants and packet parsing
├── connection.py       # Serial connection management
├── controller.py       # Main PoolController class
├── commands.py         # Temperature control commands
├── monitor.py          # Real-time monitoring
└── cli.py             # Command-line interface

tests/
├── test_protocol.py    # Protocol function tests
├── test_connection.py  # Connection tests with mocks
├── test_controller.py  # Controller integration tests
├── test_commands.py    # Command function tests
├── test_monitor.py     # Monitor functionality tests
└── test_cli.py        # CLI interface tests
```

See [CLAUDE.md](CLAUDE.md) for additional development guidance and architecture details.

## References

- Protocol documentation: `docs/protocol.txt`
- Based on Compool protocol from Cinema Online forums and MisterHouse project