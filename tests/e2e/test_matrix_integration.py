import pytest
import requests
import json
import time
import os
from urllib.parse import quote

@pytest.fixture(scope="module")
def matrix_credentials():
    """Create a test user and get access token"""
    homeserver_url = "http://localhost:8008"
    
    # Create a random username for testing
    import random
    import string
    username = ''.join(random.choices(string.ascii_lowercase, k=8))
    password = "testpassword"
    
    # Register the user
    register_data = {
        "username": username,
        "password": password,
        "auth": {"type": "m.login.dummy"}
    }
    
    try:
        response = requests.post(
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
            
            response = requests.post(
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
        pytest.skip(f"Could not create Matrix test user: {str(e)}")
    
    pytest.skip("Could not create Matrix test user")

def test_matrix_search(matrix_credentials):
    """Test that Matrix search is working through the AutonomousSphere API"""
    # Create a test room
    room_data = {
        "visibility": "private",
        "name": "Test Search Room",
        "topic": "A room for testing search functionality"
    }
    
    response = requests.post(
        f"{matrix_credentials['homeserver_url']}/_matrix/client/v3/createRoom",
        headers={"Authorization": f"Bearer {matrix_credentials['access_token']}"},
        json=room_data
    )
    
    assert response.status_code == 200
    room_id = response.json()["room_id"]
    
    # Send a test message
    test_message = "This is a unique test message for searching XYZ123"
    message_data = {
        "msgtype": "m.room.message",
        "body": test_message
    }
    
    response = requests.put(
        f"{matrix_credentials['homeserver_url']}/_matrix/client/v3/rooms/{quote(room_id)}/send/m.room.message/{int(time.time() * 1000)}",
        headers={"Authorization": f"Bearer {matrix_credentials['access_token']}"},
        json=message_data
    )
    
    assert response.status_code == 200
    
    # Wait for the message to be indexed
    time.sleep(2)
    
    # Search for the message through the AutonomousSphere API
    search_query = {
        "query": "XYZ123",
        "filters": {}
    }
    
    max_retries = 5
    for i in range(max_retries):
        response = requests.post(
            "http://localhost:8000/search/",
            headers={"Authorization": f"Bearer {matrix_credentials['access_token']}"},
            json=search_query
        )
        
        assert response.status_code == 200
        results = response.json()
        
        # Check if the message was found
        messages = results["results"]["matrix"]["messages"]
        if any(test_message in str(msg["content"]) for msg in messages):
            break
            
        if i == max_retries - 1:
            pytest.fail("Test message not found in search results")
        
        # Wait and retry
        time.sleep(2)