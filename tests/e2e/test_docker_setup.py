import pytest
import docker
import time
import requests
import psycopg2
import os

@pytest.fixture(scope="module")
def docker_environment():
    """Set up the Docker environment for testing"""
    client = docker.from_env()
    
    # Check if containers are already running
    containers = {
        "postgres": None,
        "synapse": None,
        "autonomoussphere": None
    }
    
    for container in client.containers.list():
        for name in containers.keys():
            if name in container.name:
                containers[name] = container
    
    # If containers are not running, start them
    if not all(containers.values()):
        # Pull images if needed
        print("Starting Docker containers...")
        os.system("docker-compose up -d")
        
        # Wait for containers to be ready
        max_retries = 30
        retry_interval = 2
        
        for _ in range(max_retries):
            all_running = True
            for name in containers.keys():
                try:
                    container = client.containers.get(name)
                    if container.status != "running":
                        all_running = False
                        break
                except docker.errors.NotFound:
                    all_running = False
                    break
            
            if all_running:
                break
                
            time.sleep(retry_interval)
        
        # Update container references
        for name in containers.keys():
            try:
                containers[name] = client.containers.get(name)
            except docker.errors.NotFound:
                pass
    
    yield containers
    
    # Don't stop containers after tests - they might be used by other tests or development

def test_postgres_container(docker_environment):
    """Test that the Postgres container is running and pgvector is installed"""
    postgres = docker_environment["postgres"]
    assert postgres is not None
    assert postgres.status == "running"
    
    # Test that pgvector is installed
    # Execute a command in the container to check if pgvector extension exists
    exit_code, output = postgres.exec_run(
        "psql -U synapse -d synapse -c \"SELECT * FROM pg_extension WHERE extname = 'vector';\"",
        environment={"PGPASSWORD": "synapsepass"}
    )
    
    assert exit_code == 0
    assert b"vector" in output

def test_synapse_container(docker_environment):
    """Test that the Synapse container is running and responding to API requests"""
    synapse = docker_environment["synapse"]
    assert synapse is not None
    assert synapse.status == "running"
    
    # Test that Synapse API is responding
    max_retries = 10
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8008/_matrix/client/versions")
            if response.status_code == 200:
                assert "versions" in response.json()
                break
        except requests.exceptions.ConnectionError:
            if i == max_retries - 1:
                pytest.fail("Could not connect to Synapse API")
            time.sleep(retry_interval)

def test_autonomoussphere_container(docker_environment):
    """Test that the AutonomousSphere container is running and responding to API requests"""
    autonomoussphere = docker_environment["autonomoussphere"]
    assert autonomoussphere is not None
    assert autonomoussphere.status == "running"
    
    # Test that AutonomousSphere API is responding
    max_retries = 10
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:29333/health")
            if response.status_code == 200:
                assert response.json()["status"] == "healthy"
                break
        except requests.exceptions.ConnectionError:
            if i == max_retries - 1:
                pytest.fail("Could not connect to AutonomousSphere API")
            time.sleep(retry_interval)