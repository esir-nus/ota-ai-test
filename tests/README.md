# OTA Daemon Test Suite

This directory contains unit and integration tests for the OTA daemon, along with utilities for setting up a test environment.

## Test Structure

- **Unit Tests**: Test individual components in isolation
  - `test_scheduler.py`: Tests for the TaskScheduler component
  - `test_backup_system.py`: Tests for the BackupManager component
  
- **Integration Tests**: Test multiple components working together
  - `test_integration.py`: End-to-end tests with a mock server

## Prerequisites

The tests require the following Python packages:

- `pytest`
- `pytest-cov`
- `coverage`
- `mock`

You can install these dependencies with:

```
pip install pytest pytest-cov coverage mock
```

## Setting Up the Test Environment

For testing on Raspberry Pi or a similar environment, use the setup script:

```
sudo bash setup_test_environment.sh
```

This script will:
1. Create necessary directories
2. Set appropriate permissions
3. Create a test device ID
4. Create a test OTA configuration
5. Install required dependencies

## Running the Tests

You can run all tests using the test runner script:

```
python run_tests.py
```

This will:
1. Run all unit and integration tests
2. Generate a coverage report in the terminal
3. Create an HTML coverage report in the `coverage_html` directory

To run individual test files:

```
python -m unittest tests.test_scheduler
python -m unittest tests.test_backup_system
python -m unittest tests.test_integration
```

## Creating Mock Server for Testing

The integration tests use a mock HTTP server that simulates the OTA update server. This server provides:

1. A manifest endpoint (`/api/update/manifest`)
2. An update file endpoint (`/updates/test_file.txt`)
3. A status reporting endpoint (`/api/update/report`)

You can extend this mock server for additional testing needs by modifying the `MockOTAServer` class in `test_integration.py`.

## Testing on Raspberry Pi

For testing on an actual Raspberry Pi:

1. Set up the test environment: `sudo bash setup_test_environment.sh`
2. Run the tests: `python -m tests.run_tests`
3. Check the coverage report to identify any untested code paths

## Troubleshooting

- If you encounter permission issues, make sure the script has been run with sudo
- For import errors, make sure you're running the tests from the correct directory
- If the integration tests fail, check if port 8000 is already in use 