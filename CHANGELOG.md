# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive GitHub Actions CI/CD workflows
- Pre-commit configuration for local development
- CONTRIBUTING.md with development guidelines
- Comprehensive test coverage (94%)
- Professional Python package structure

## [0.1.0] - 2024-12-18

### Added
- Initial release of pycompool
- RS-485 communication with Pentair/Compool LX3xxx controllers
- Pool and spa temperature control commands
- Real-time heartbeat packet monitoring
- Command-line interface with Fire framework
- Protocol parsing for temperature and status data
- Serial connection management with context managers
- Comprehensive test suite with mocked connections
- Modern Python packaging with pyproject.toml
- Ruff linting and mypy type checking
- Documentation and README

### Features
- `compoolctl set-pool <temp>` - Set pool temperature
- `compoolctl set-spa <temp>` - Set spa temperature  
- `compoolctl monitor` - Real-time monitoring of heartbeat packets
- Support for both hardware RS-485 and network connections
- Temperature encoding/decoding (0.25°C for water, 0.5°C for air/solar)
- Graceful signal handling for monitoring mode

### Technical Details
- Supports Python 3.9-3.13
- Built with modern tooling (uv, ruff, pytest, mypy)
- Modular architecture separating protocol, connection, and control logic
- Comprehensive error handling and logging
- Type hints throughout codebase