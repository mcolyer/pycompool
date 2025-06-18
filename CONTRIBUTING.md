# Contributing to pycompool

Thank you for your interest in contributing to pycompool! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/mcolyer/pycompool.git
   cd pycompool
   ```

2. **Install development dependencies**
   ```bash
   uv sync --extra dev
   ```

3. **Install pre-commit hooks** (recommended)
   ```bash
   uv run pre-commit install
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/pycompool --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_protocol.py
```

### Code Quality

```bash
# Run linter
uv run ruff check

# Auto-fix linting issues
uv run ruff check --fix

# Format code
uv run ruff format

# Type checking
uv run mypy src/pycompool
```

### Testing the CLI

```bash
# Test CLI commands
uv run compoolctl --help
uv run compoolctl set-pool --help
```

## Code Standards

### Style Guidelines

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Line length: 88 characters (configured in ruff)

### Testing

- Write tests for all new functionality
- Aim for high test coverage (>90%)
- Use mocks for serial connections and external dependencies
- Test both success and error cases

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in imperative mood
- Reference issues when applicable

Example:
```
Add support for temperature monitoring

- Implement parse_heartbeat_packet function
- Add PoolMonitor class for real-time monitoring  
- Include tests with mock serial connections

Fixes #123
```

## Project Structure

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

## Making Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following the style guidelines
   - Add or update tests as needed
   - Update documentation if applicable

3. **Test your changes**
   ```bash
   uv run pytest
   uv run ruff check
   uv run mypy src/pycompool
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Use the GitHub web interface to create a PR
   - Provide a clear description of your changes
   - Reference any related issues

## CI/CD

The project uses GitHub Actions for:

- **Linting**: ruff and mypy checks
- **Testing**: pytest across Python 3.9-3.13
- **Package building**: Verify package can be built and installed
- **Releases**: Automatic PyPI publishing for tagged releases

## Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues and PRs before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.