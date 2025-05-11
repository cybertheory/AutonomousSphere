import os
import sys
import pytest
import asyncio
import httpx
import yaml
import time
from fastapi.testclient import TestClient
from fastapi import FastAPI
import docker

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the main application
from main import app

# Fixture for the FastAPI test client
@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

# Fixture for async test client
@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

# Fixture for test configuration
@pytest.fixture
def test_config():
    config_path = os.path.join(os.path.dirname(__file__), "test_config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# Fixture for Docker client
@pytest.fixture
def docker_client():
    return docker.from_env()

# Fixture to wait for services to be ready
@pytest.fixture(scope="session")
def wait_for_services():
    # Wait for services to be up (used in integration tests)
    max_retries = 30
    retry_interval = 2
    
    # Define service endpoints to check
    endpoints = {
        "synapse": "http://localhost:8008/_matrix/client/versions",
        "autonomoussphere": "http://localhost:8000/registry/health",
    }
    
    for service, url in endpoints.items():
        for i in range(max_retries):
            try:
                response = httpx.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"{service} is ready!")
                    break
            except (httpx.ConnectError, httpx.ReadTimeout):
                pass
            
            if i < max_retries - 1:
                print(f"Waiting for {service}... ({i+1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                pytest.fail(f"Service {service} did not become ready in time")