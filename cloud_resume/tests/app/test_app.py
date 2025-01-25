import pytest
import cloud_resume.app as cloud_resume
from cloud_resume.db import FirestoreClient
from flask import request
from datetime import datetime, timezone, timedelta

@pytest.fixture
def test_app():
    app = cloud_resume.app
    app.config.update({
        'TESTING': True,
    })

    yield app

@pytest.fixture
def client(test_app):
    return test_app.test_client()

def test_index(mocker, test_app, client):
    mocker.patch("cloud_resume.app.increment_counter", return_value=1)

    response = client.get('/')
    with test_app.test_request_context():
        print(request.user_agent.string)
    assert response.status_code == 200
    assert b'<title>Steven Rupert' in response.data

def test_counter_integration(setup_firestore_emulator, client, monkeypatch, mocker):
    firestore_port = setup_firestore_emulator
    monkeypatch.setenv('FIRESTORE_EMULATOR_HOST', f'localhost:{firestore_port}')

    # Test Counter is initialized to 1.
    response = client.get('/')
    assert b'<b>You are visitor number: 1' in response.data
    
    # Counter shouldn't increment on visits within 24 hours.
    response = client.get('/')
    assert b'<b>You are visitor number: 1' in response.data
    
    # Counter should increment on visit from new user.
    response = client.get('/', headers={"X-Forwarded-For": "10.0.10.1"})
    assert b'<b>You are visitor number: 2' in response.data

    # Counter should increment when user visits 24 hours later.
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    database = FirestoreClient()
    database.connect_to_firestore()
    database._db.collection('visitor_ips').document('10.0.10.1').set({'timestamp': one_day_ago})
    monkeypatch.setattr('cloud_resume.db.ip_cache', {})
    response = client.get('/', headers={"X-Forwarded-For": "10.0.10.1"})
    assert b'<b>You are visitor number: 3' in response.data