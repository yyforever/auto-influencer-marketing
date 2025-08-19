#!/bin/bash

# Test runner script for auto influencer marketing platform
# Usage: ./run_tests.sh [test_type]
# Test types: unit, integration, all (default)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated
check_venv() {
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        print_warning "Virtual environment not activated. Activating..."
        source .venv/bin/activate || {
            print_error "Failed to activate virtual environment. Please run: source .venv/bin/activate"
            exit 1
        }
    fi
    print_status "Virtual environment: $VIRTUAL_ENV"
}

# Install dependencies if needed
install_deps() {
    print_status "Checking development dependencies..."
    if ! python -c "import pytest" 2>/dev/null; then
        print_status "Installing development dependencies..."
        uv sync --group dev
    fi
}

# Run tests based on type
run_tests() {
    local test_type=${1:-"all"}
    
    print_status "Running $test_type tests..."
    
    case $test_type in
        "unit")
            python -m pytest tests/ -m "unit" -v --tb=short
            ;;
        "integration") 
            python -m pytest tests/ -m "integration" -v --tb=short
            ;;
        "influencer")
            python -m pytest tests/test_influencer_search_tool.py -v --tb=short
            ;;
        "all"|*)
            python -m pytest tests/ -v --tb=short
            ;;
    esac
}

# Show coverage report
show_coverage() {
    if command -v pytest-cov &> /dev/null; then
        print_status "Generating coverage report..."
        python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html
        print_status "HTML coverage report generated in htmlcov/"
    else
        print_warning "pytest-cov not installed. Install with: uv add --group dev pytest-cov"
    fi
}

# Main execution
main() {
    print_status "Auto Influencer Marketing Platform - Test Runner"
    print_status "=============================================="
    
    check_venv
    install_deps
    run_tests "$1"
    
    if [[ "$2" == "--coverage" ]]; then
        show_coverage
    fi
    
    print_status "Tests completed successfully! ✅"
}

# Help message
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [test_type] [--coverage]"
    echo ""
    echo "Test types:"
    echo "  all         Run all tests (default)"
    echo "  unit        Run only unit tests"
    echo "  integration Run only integration tests"
    echo "  influencer  Run only influencer search tool tests"
    echo ""
    echo "Options:"
    echo "  --coverage  Generate coverage report"
    echo "  --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 unit               # Run unit tests only"
    echo "  $0 all --coverage     # Run all tests with coverage"
    exit 0
fi

main "$@"