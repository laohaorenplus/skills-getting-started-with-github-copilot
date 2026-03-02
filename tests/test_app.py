import pytest
from copy import deepcopy
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)

# keep a snapshot of the initial activities to restore between tests
INITIAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    # Restore the in-memory activities to a clean state before each test
    app_module.activities.clear()
    app_module.activities.update(deepcopy(INITIAL_ACTIVITIES))
    yield
    # also restore after the test to be safe
    app_module.activities.clear()
    app_module.activities.update(deepcopy(INITIAL_ACTIVITIES))


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_participant_present():
    email = "newstudent@example.com"
    resp = client.post("/activities/Chess%20Club/signup", params={"email": email})
    assert resp.status_code == 200
    assert "Signed up" in resp.json().get("message", "")

    # Verify participant was added
    activities = client.get("/activities").json()
    assert email in activities["Chess Club"]["participants"]


def test_duplicate_signup_returns_400():
    email = "emma@mergington.edu"  # already signed up in initial data
    resp = client.post("/activities/Programming%20Class/signup", params={"email": email})
    assert resp.status_code == 400


def test_unregister_participant():
    email = "toremove@example.com"
    # add participant first
    r = client.post("/activities/Chess%20Club/signup", params={"email": email})
    assert r.status_code == 200

    # remove participant
    resp = client.delete("/activities/Chess%20Club/participants", params={"email": email})
    assert resp.status_code == 200
    assert "Unregistered" in resp.json().get("message", "")

    # ensure participant is no longer present
    activities = client.get("/activities").json()
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_nonexistent_returns_404():
    resp = client.delete("/activities/Chess%20Club/participants", params={"email": "noone@example.com"})
    assert resp.status_code == 404
