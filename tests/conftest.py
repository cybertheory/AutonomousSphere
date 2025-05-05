import pytest
import os
import asyncio
import aiohttp
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi.testclient import TestClient
import sys
from unittest.mock import AsyncMock, patch

# Add the parent directory to the path so we can import the application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db.database import Base, get_db
from api.main import app
from api.pubsub.broker import broker
from api.pubsub.a2a_client import get_a2a_integration

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql://postgres:postgres@db:5432/test_autonomoussphere"
)

# Create test database engine
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def mock_a2a_integration():
    with patch("api.pubsub.a2a_client.get_a2a_integration") as mock:
        mock_integration = AsyncMock()
        mock.return_value = mock_integration
        yield mock_integration

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def db_engine():
    """Create a test database engine."""
    # Create the test database
    Base.metadata.create_all(bind=engine)
    yield engine
    # Drop the test database
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(db_engine):
    """Create a new database session for a test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Create a test client for the FastAPI application."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    # Override the get_db dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Add this line to bypass authentication in tests
    # This assumes you have a get_current_active_user dependency in your routes
    from api.services.auth_service import get_current_active_user
    
    # Create a mock user for testing
    async def mock_current_user():
        from api.schemas.user import User
        return User(id=1, username="test_user", email="test@example.com", is_active=True)
    
    # Override the authentication dependency
    app.dependency_overrides[get_current_active_user] = mock_current_user
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear all overrides after the test
    app.dependency_overrides.clear()

@pytest.fixture
async def http_session():
    """Create an aiohttp session for async tests."""
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.fixture(scope="session")
def wait_for_services():
    """Wait for all services to be available."""
    max_retries = 30
    retry_interval = 2
    
    services = {
        "api": "http://api:8000/health",
        "registry": "http://registry:8081/health",
        "example_agent": "http://example-agent:8080/health"
    }
    
    for service_name, url in services.items():
        retries = 0
        while retries < max_retries:
            try:
                import requests
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"Service {service_name} is available")
                    break
            except Exception:
                pass
            
            print(f"Waiting for {service_name} to be available...")
            time.sleep(retry_interval)
            retries += 1
        
        if retries == max_retries:
            pytest.fail(f"Service {service_name} is not available after {max_retries} retries")
    
    # Additional wait to ensure services are fully initialized
    time.sleep(5)
    return True

@pytest.fixture
async def test_broker():
    """Create a test broker instance."""
    # Use the existing broker but clear all subscribers
    broker.subscribers = {}
    broker.channel_subscribers = {}
    broker.dm_subscribers = {}
    broker.active_connections = {}
    broker.user_connections = {}
    
    yield broker

@pytest.fixture
async def test_a2a_integration():
    """Create a test A2A integration instance."""
    # Use the existing a2a_integration but clear all agents
    a2a_integration = get_a2a_integration()
    a2a_integration.agents = {}
    
    yield a2a_integration