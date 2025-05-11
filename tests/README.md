# AutonomousSphere Tests

This directory contains tests for the AutonomousSphere project. The tests are organized into three categories:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test interactions between components
3. **End-to-End Tests**: Test the entire system

## Test Structure

```
tests/
├── conftest.py           # Common test fixtures and configuration
├── test_config.yaml      # Test configuration
├── utils.py              # Test utility functions
├── run_tests.py          # Test runner script
├── unit/                 # Unit tests
│   ├── test_registry.py  # Tests for the registry component
│   ├── test_search.py    # Tests for the search component
│   └── test_mcp.py       # Tests for the MCP component
├── integration/          # Integration tests
│   ├── test_registry_api.py    # Tests for the registry API
│   ├── test_search_api.py      # Tests for the search API
│   └── test_mcp_registration.py # Tests for MCP registration
└── e2e/                  # End-to-end tests
    ├── test_docker_setup.py    # Tests for Docker environment
    ├── test_matrix_integration.py # Tests for Matrix integration
    └── test_mcp_functionality.py  # Tests for MCP functionality
```

## Running Tests

You can run the tests using the provided `run_tests.py` script:

```bash
# Run all tests
python tests/run_tests.py

# Run only unit tests
python tests/run_tests.py --type unit

# Run only integration tests
python tests/run_tests.py --type integration

# Run only end-to-end tests
python tests/run_tests.py --type e2e

# Run tests with verbose output
python tests/run_tests.py --verbose
```

Alternatively, you can use pytest directly:

```bash
# Run all tests
pytest tests/

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only end-to-end tests
pytest tests/e2e/
```

## Test Requirements

The tests require the following dependencies:

- pytest
- pytest-asyncio
- pytest-cov
- httpx
- docker-py
- websockets
- psycopg2-binary

These dependencies are included in the project's `pyproject.toml` file.

## Docker Environment

The integration and end-to-end tests require the Docker environment to be running. The `run_tests.py` script will automatically check and start the Docker environment if needed.

If you want to skip the Docker environment check/start, you can use the `--no-docker` flag:

```bash
python tests/run_tests.py --no-docker
```

## Test Coverage

The tests generate coverage reports in both terminal output and HTML format. The HTML coverage report is saved to `tests/coverage/index.html`.
```