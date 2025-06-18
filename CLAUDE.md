# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python package for controlling Pentair/Compool LX3xxx pool and spa systems via RS-485 serial communication. The project provides a command-line tool `compoolctl` that can set pool and spa temperatures.

## Architecture

This is a Python library with a CLI interface for controlling pool systems via RS-485.

### Package Structure

- **src/pycompool/**: Main library package
  - `protocol.py`: Protocol constants, packet parsing, temperature conversions
  - `connection.py`: Serial connection management with context managers
  - `controller.py`: High-level `PoolController` class API
  - `commands.py`: Command implementations for CLI
  - `monitor.py`: Real-time monitoring with `PoolMonitor` class
  - `cli.py`: Fire-based CLI interface
- **tests/**: Comprehensive test suite with mocks
- **docs/**: Protocol documentation

### Key Classes

- `PoolController`: Main API for setting temperatures
- `PoolMonitor`: Real-time heartbeat packet monitoring
- `SerialConnection`: Connection management with RS-485 support
- `CLI`: Fire-based command-line interface

## Development Commands

```bash
# Install dependencies (uses uv package manager)
uv sync --extra dev

# Install pre-commit hooks (recommended)
uv run pre-commit install

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/pycompool --cov-report=term-missing

# Run linter
uv run ruff check

# Auto-fix linting issues  
uv run ruff check --fix

# Format code
uv run ruff format

# Type checking
uv run mypy src/pycompool

# Run CLI
uv run compoolctl set-pool 80f
uv run compoolctl monitor

# Test with different serial configurations
COMPOOL_PORT=socket://192.168.0.50:8899 uv run compoolctl set-pool 90f

# Build package
uv build
```

## CI/CD

GitHub Actions workflows:
- **CI**: Linting, testing across Python 3.9-3.13, package building
- **Release**: Automatic PyPI publishing on version tags
- **Path filtering**: Only runs on code changes (ignores README/docs changes)

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