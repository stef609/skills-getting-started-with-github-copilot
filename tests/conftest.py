"""
Pytest configuration and shared fixtures for testing the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient
import src.app as app_module


# Sample test data with initial participants
TEST_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 3,  # Small capacity for testing
        "participants": ["emma@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 2,  # Very small for testing capacity limits
        "participants": ["john@mergington.edu"]
    }
}


@pytest.fixture
def client():
    """
    Provide a TestClient with a fresh copy of activities for each test.
    This ensures test isolation and prevents state leakage between tests.
    """
    # Deep copy the activities dictionary to provide a fresh state for each test
    import copy
    original_activities = copy.deepcopy(app_module.activities)
    app_module.activities = copy.deepcopy(TEST_ACTIVITIES)
    
    yield TestClient(app_module.app)
    
    # Restore original activities after test
    app_module.activities = original_activities
