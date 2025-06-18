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

- `PoolController`: Main API for setting temperatures and heater modes
- `PoolMonitor`: Real-time heartbeat packet monitoring
- `SerialConnection`: Connection management with RS-485 support
- `CLI`: Fire-based command-line interface

## Development Commands

```bash
# Install dependencies (uses uv package manager)
uv sync --extra dev

# Install pre-commit hooks (recommended)
uv run pre-commit install

# Run full quality checks (like CI)
uv run pytest && uv run ruff check && uv run mypy src/pycompool

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
uv run compoolctl set-heater heater pool
uv run compoolctl monitor

# Test with different serial configurations
COMPOOL_PORT=socket://192.168.0.50:8899 uv run compoolctl set-pool 90f
COMPOOL_PORT=socket://192.168.0.50:8899 uv run compoolctl set-heater solar-only spa

# Build package
uv build

# Create and test release
git tag -a v0.1.1 -m "Release v0.1.1"
git push origin v0.1.1
```

## CI/CD

GitHub Actions workflows:
- **CI**: Linting, testing across Python 3.9-3.13, package building
- **Release**: Automatic PyPI publishing on version tags using trusted publishing
- **Path filtering**: Only runs on code changes (ignores README/docs changes)

### Release Process

1. Update version in `pyproject.toml` and `src/pycompool/__init__.py`
2. Update `CHANGELOG.md` with new version entry
3. Create and push version tag: `git tag -a v0.1.1 -m "Release message"`
4. GitHub Actions will automatically build and publish to PyPI

### Common Issues

- **MyPy type errors**: Ensure all functions have return type annotations
  - Use `Generator[ReturnType, None, None]` from `collections.abc` for generators
  - Use `Any` from `typing` for signal handler frame parameters
  - Handle `Optional[str]` returns from `os.getenv()` properly
- **Import organization**: Ruff will auto-fix import sorting with `--fix`
- **Pre-commit hooks**: Run `uv run pre-commit install` after cloning

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
- Heat source control using bits 4-7 (bit 4 enables, bits 4-5 for pool, bits 6-7 for spa)

## Monitoring and Connection Issues

### Packet Buffering
When using network-based serial connections (socket://), packets may be buffered and delivered in bursts rather than real-time. To minimize this:
- The monitor reads 24-byte chunks (matching packet size)
- Extended timeout (30s) prevents premature disconnection
- Consider implementing packet deduplication for repeated identical packets

### Network Serial Bridges
Serial-to-network bridges may introduce latency and buffering:
- Test with different timeout values if packets arrive in bursts
- Check bridge settings for real-time mode or reduced buffering
- Monitor verbose output shows exact packet timing and content

### Common Debugging
- Use `--verbose` flag to see raw packet data and timing
- Check that heartbeat packets arrive every ~2.5 seconds as expected
- Verify packet structure starts with sync bytes `FF AA`
- Monitor for connection drops vs. controller stopping transmission