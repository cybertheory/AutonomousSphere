#!/bin/bash

# Create Docker network if it doesn't exist
echo "Ensuring network exists..."
docker network inspect autonomoussphere-network >/dev/null 2>&1 || docker network create autonomoussphere-network

# Create the test database
echo "Creating test database..."
docker-compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS test_autonomoussphere;"
docker-compose exec db psql -U postgres -c "CREATE DATABASE test_autonomoussphere;"

# Run the tests
echo "Running tests..."
docker-compose -f docker-compose.yml -f docker-compose.test.yml up --build test

# Capture the exit code
TEST_EXIT_CODE=$?

# Clean up
echo "Cleaning up..."
docker-compose -f docker-compose.yml -f docker-compose.test.yml down test

# Exit with the test exit code
exit $TEST_EXIT_CODE
