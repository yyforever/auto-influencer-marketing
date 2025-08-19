# Tests for Auto Influencer Marketing Platform

This directory contains comprehensive tests for the backend components of the auto influencer marketing platform.

## Test Structure

- `test_influencer_search_tool.py` - Comprehensive tests for the influencer search tool functionality

## Running Tests

### Prerequisites

Make sure you have the development dependencies installed:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dev dependencies
uv sync --group dev
```

### Running All Tests

```bash
# Run all tests with verbose output
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_influencer_search_tool.py -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

### Running Specific Tests

```bash
# Run only unit tests (if marked)
python -m pytest tests/ -m unit

# Run only integration tests (if marked) 
python -m pytest tests/ -m integration

# Run specific test method
python -m pytest tests/test_influencer_search_tool.py::TestInfluencerSearchTool::test_basic_functionality
```

## Test Configuration

Tests are configured in `pyproject.toml` with the following settings:

- **Async mode**: Automatic async test detection and execution
- **Test paths**: `tests/` directory
- **Markers**: Support for `unit`, `integration`, and `asyncio` markers
- **Output**: Verbose mode with short traceback format

## Test Coverage

The test suite covers:

### Influencer Search Tool (`test_influencer_search_tool.py`)
- ✅ **Basic functionality** - Normal API responses and result formatting
- ✅ **Parameter validation** - Platform validation, keyword formatting, limits
- ✅ **Error handling** - Network errors, API errors, HTTP status codes
- ✅ **Edge cases** - Empty results, missing data, null values
- ✅ **Configuration** - Environment variables, default parameters
- ✅ **URL construction** - Multi-platform endpoint generation
- ✅ **Result parsing** - Response parsing and formatting logic

### Test Features
- **Mocked HTTP requests** - No external API dependencies during testing
- **Async support** - Full async/await test coverage
- **Parametrized tests** - Multiple scenarios with single test methods
- **Fixture-based setup** - Reusable test data and configurations

## Adding New Tests

When adding new tests:

1. Create test files with `test_*.py` naming convention
2. Use `TestClassName` for test classes
3. Use `test_method_name` for test methods  
4. Add async tests with `@pytest.mark.asyncio` decorator
5. Use fixtures for reusable test data
6. Mock external dependencies (APIs, databases, etc.)

Example test structure:

```python
import pytest
from unittest.mock import patch, AsyncMock

class TestNewFeature:
    """Test suite for new feature."""
    
    @pytest.fixture
    def sample_data(self):
        """Sample test data."""
        return {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_new_functionality(self, sample_data):
        """Test new functionality with sample data."""
        with patch('module.external_call') as mock_call:
            mock_call.return_value = sample_data
            result = await new_function()
            assert result == expected_result
```

## Dependencies

Test dependencies are managed in `pyproject.toml`:

- `pytest>=8.3.5` - Testing framework
- `pytest-asyncio>=0.23.0` - Async test support
- `pytest-mock>=3.12.0` - Mocking utilities

Additional testing tools can be added to the `dev` dependency group as needed.