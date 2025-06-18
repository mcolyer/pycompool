# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Heater control command `set-heater` for controlling heating modes
- Support for four heating modes: off, heater, solar-priority, solar-only
- Comprehensive unit tests for heater control functionality
- Extended timeout support for monitoring to handle connection delays
- `get_status()` method to PoolController for retrieving single heartbeat packet status

### Fixed
- Packet buffering issues in monitor causing burst delivery of stale packets
- Reduced read chunk size from 64 to 24 bytes for smoother real-time monitoring
- Linting issues with trailing whitespace in test files

### Changed
- Monitor timeout increased from 1s to 30s to handle longer delays between packets
- Improved monitoring stability for network-based serial connections

## [0.1.1] - 2024-12-18

### Added
- Comprehensive CHANGELOG.md with version history
- MIT LICENSE file for open source compliance
- CONTRIBUTING.md with development guidelines
- Pre-commit configuration for local development
- Comprehensive GitHub Actions CI/CD workflows with PyPI trusted publishing

### Fixed
- MyPy type annotation errors in connection.py and monitor.py
- Import organization and code formatting issues
- Removed .coverage file from version control

### Changed
- Updated release workflow to use PyPI trusted publishing (more secure)
- Enhanced release workflow with full quality checks
- Updated CLAUDE.md with development best practices and troubleshooting

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