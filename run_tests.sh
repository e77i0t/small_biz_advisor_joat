#!/bin/bash
set -e

# Ensure reports directory exists
mkdir -p reports/junit

# Start test database and message broker (assumes docker-compose.dev.yml is set up)
echo "Starting test database and message broker..."
docker-compose -f docker-compose.dev.yml up -d
sleep 10  # Wait for services to be ready

# Run unit and shared tests with coverage
echo "Running unit and shared tests with coverage..."
pytest --cov=communication_platform --cov-report=term-missing --cov-report=xml --junitxml=reports/junit/unit-shared.xml -m "unit or not integration and not performance" communication-platform/tests/services communication-platform/tests/shared

# Run integration tests
echo "Running integration tests..."
pytest --junitxml=reports/junit/integration.xml -m integration communication-platform/tests/integration

# Run performance tests with pass/fail thresholds
echo "Running performance tests..."
pytest --benchmark-only --benchmark-min-rounds=5 --benchmark-autosave --junitxml=reports/junit/performance.xml -m performance communication-platform/tests/performance

# Stop test services
echo "Stopping test database and message broker..."
docker-compose -f docker-compose.dev.yml down

echo "All tests complete. Coverage and JUnit XML reports are in the reports/junit directory." 