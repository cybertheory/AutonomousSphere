import asyncio
import httpx
import json
import time
import os
import yaml
import psycopg2
from typing import Dict, Any, Optional

# Load test configuration
def load_test_config():
    config_path = os.path.join(os.path.dirname(__file__), "test_config.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# Create a Matrix test user
async def create_matrix_test_user(username: str, password: str) -> Dict[str, Any]:
    """Create a test user on the Matrix homeserver and return credentials"""
    config = load_test_config()
    homeserver_url = config["homeserver"]["address"]
    
    # Register the user
    register_data = {
        "username": username,
        "password": password,
        "auth": {"type": "m.login.dummy"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{homeserver_url}/_matrix/client/v3/register",
                json=register_data
            )
            
            if response.status_code == 200:
                credentials = response.json()
                return {
                    "user_id": credentials["user_id"],
                    "access_token": credentials["access_token"],
                    "homeserver_url": homeserver_url
                }
            else:
                # Try logging in instead
                login_data = {
                    "type": "m.login.password",
                    "user": username,
                    "password": password
                }
                
                response = await client.post(
                    f"{homeserver_url}/_matrix/client/v3/login",
                    json=login_data
                )
                
                if response.status_code == 200:
                    credentials = response.json()
                    return {
                        "user_id": credentials["user_id"],
                        "access_token": credentials["access_token"],
                        "homeserver_url": homeserver_url
                    }
        except Exception as e:
            print(f"Error creating Matrix test user: {str(e)}")
    
    return None

# Connect to the Postgres database
def connect_to_db():
    """Connect to the Postgres database and return connection"""
    config = load_test_config()
    db_config = config["database"]
    
    try:
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            user=db_config["user"],
            password=db_config["password"],
            database=db_config["database"]
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return None

# Wait for a service to be ready
async def wait_for_service(url: str, max_retries: int = 30, retry_interval: int = 2) -> bool:
    """Wait for a service to be ready by polling the URL"""
    async with httpx.AsyncClient() as client:
        for i in range(max_retries):
            try:
                response = await client.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except (httpx.ConnectError, httpx.ReadTimeout):
                pass
            
            if i < max_retries - 1:
                await asyncio.sleep(retry_interval)
    
    return False