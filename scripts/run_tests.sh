#!/bin/bash

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# Create Docker network if it doesn't exist
echo "Ensuring network exists..."
docker network inspect autonomoussphere-network >/dev/null 2>&1 || docker network create autonomoussphere-network

# Start all required services
echo "Starting required services..."
docker-compose up -d api db redis registry example-agent

# Wait for services to initialize
echo "Waiting for services to initialize..."
sleep 20

# Create the test database
echo "Creating test database..."
docker-compose exec db psql -U postgres -c "DROP DATABASE IF EXISTS test_autonomoussphere;"
docker-compose exec db psql -U postgres -c "CREATE DATABASE test_autonomoussphere;"

#restarting
echo "Stopping existing containers..."
docker-compose down

# Run the tests
echo "Running tests..."
docker-compose -f docker-compose.yml -f docker-compose.test.yml up --build test

# Capture the exit code
TEST_EXIT_CODE=$?

# Clean up
echo "Cleaning up..."
docker-compose down

# Exit with the test exit code
exit $TEST_EXIT_CODE
