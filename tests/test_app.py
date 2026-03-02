import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app as fastapi_app, activities

client = TestClient(fastapi_app)

# keep an original snapshot for resetting state
_ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange: clear and repopulate the in-memory store before each test
    activities.clear()
    activities.update(copy.deepcopy(_ORIGINAL_ACTIVITIES))
    yield
    # no cleanup necessary, fixture scope is function


def test_get_activities_returns_initial_data():
    # Arrange: fixture has reset activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == _ORIGINAL_ACTIVITIES


def test_successful_signup_adds_participant():
    # Arrange
    email = "new@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert "Signed up" in response.json()["message"]
    assert email in activities[activity_name]["participants"]


def test_duplicate_signup_returns_400():
    # Arrange
    email = _ORIGINAL_ACTIVITIES["Chess Club"]["participants"][0]
    activity_name = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_unregister_removes_participant():
    # Arrange
    activity_name = "Chess Club"
    email = _ORIGINAL_ACTIVITIES[activity_name]["participants"][0]

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert "Unregistered" in response.json()["message"]
    assert email not in activities[activity_name]["participants"]


def test_unregister_nonexistent_email_returns_404():
    # Arrange
    activity_name = "Chess Club"
    email = "ghost@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found in activity"


def test_root_redirects_to_static():
    # Arrange

    # Act
    response = client.get("/")

    # Assert
    # TestClient may automatically follow the redirect, returning the page itself.
    if response.status_code in (200, 307):
        # if redirect status, check header; otherwise ensure HTML content
        if response.status_code == 307:
            assert "/static/index.html" in response.headers.get("location", "")
        else:
            assert "<!doctype html" in response.text.lower()
    else:
        pytest.fail(f"Unexpected status {response.status_code}")
