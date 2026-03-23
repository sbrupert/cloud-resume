import pytest
import re
import cloud_resume.app as cloud_resume
import cloud_resume.db as db
from flask import request
from pathlib import Path
from datetime import datetime, timezone, timedelta

def assert_counter_value(response, expected: int):
    expected_attr = f'data-counter="{expected}"'.encode()
    assert expected_attr in response.data

def assert_global_chrome(response):
    assert b'href="/"' in response.data
    assert b"Resume" in response.data
    assert b'href="/project_overview"' in response.data
    assert b"Project Overview" in response.data
    assert b"View GitHub Repo" in response.data
    assert b"https://github.com/sbrupert/cloud-resume" in response.data
    assert b"https://www.linkedin.com/in/steven-rupert-a34405197" in response.data
    assert b'href="https://github.com/sbrupert"' in response.data
    assert b"Site Version" in response.data
    assert b'id="mobile-nav-toggle"' in response.data
    assert b'id="mobile-nav-menu"' in response.data
    assert b'aria-controls="mobile-nav-menu"' in response.data
    assert b'data-mobile-nav-link' in response.data

def assert_static_frontend_assets(response):
    assert b'href="/static/css/site.css"' in response.data
    assert b"cdn.tailwindcss.com" not in response.data
    assert b"fonts.googleapis.com" not in response.data

def assert_active_nav(response, active_nav: str):
    html = response.get_data(as_text=True)
    active_targets = {
        "resume": ("/", "Resume"),
        "project_overview": ("/project_overview", "Project Overview"),
    }
    href, label = active_targets[active_nav]
    pattern = (
        r'<a\s+class="[^"]*border-b-2[^"]*"[^>]*href="'
        + re.escape(href)
        + r'"[^>]*>\s*'
        + re.escape(label)
        + r"\s*</a>"
    )
    assert re.search(pattern, html, re.S), f"Expected '{label}' to be active"

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
    assert_global_chrome(response)
    assert_static_frontend_assets(response)
    assert_active_nav(response, "resume")

def test_project_overview(client):
    response = client.get('/project_overview')
    assert response.status_code == 200
    assert b"<title>Cloud Resume | Project Overview" in response.data
    assert b"Project Overview" in response.data
    assert b"/page/project" in response.data
    assert_global_chrome(response)
    assert_static_frontend_assets(response)
    assert_active_nav(response, "project_overview")

def test_healthz(client):
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

def test_markdown_pages_are_auto_routable(client):
    pages_dir = Path(cloud_resume.app.root_path) / "pages"
    slugs = sorted(
        page_file.relative_to(pages_dir).with_suffix("").as_posix()
        for page_file in pages_dir.rglob("*.md")
    )
    assert slugs

    for slug in slugs:
        response = client.get(f"/page/{slug}")
        assert response.status_code == 200, f"Expected /page/{slug} to be routable"

def test_markdown_page_uses_global_chrome_and_project_overview_active(client):
    pages_dir = Path(cloud_resume.app.root_path) / "pages"
    slugs = sorted(
        page_file.relative_to(pages_dir).with_suffix("").as_posix()
        for page_file in pages_dir.rglob("*.md")
    )
    assert slugs

    response = client.get(f"/page/{slugs[0]}")
    assert response.status_code == 200
    assert_global_chrome(response)
    assert_static_frontend_assets(response)
    assert_active_nav(response, "project_overview")

def test_project_route_removed(client):
    response = client.get('/project')
    assert response.status_code == 404

def test_counter_integration(setup_firestore_emulator, client, monkeypatch, mocker):
    firestore_port = setup_firestore_emulator
    monkeypatch.setenv('FIRESTORE_EMULATOR_HOST', f'localhost:{firestore_port}')

    # Test Counter is initialized to 1.
    response = client.get('/')
    assert_counter_value(response, 1)
    
    # Counter shouldn't increment on visits within 24 hours.
    response = client.get('/')
    assert_counter_value(response, 1)
    
    # Counter should increment on visit from new user.
    response = client.get('/', headers={"X-Forwarded-For": "10.0.10.1"})
    assert_counter_value(response, 2)

    # Counter should increment when user visits 24 hours later.
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    database = db.FirestoreClient()
    database.connect_to_firestore()
    database._db.collection('visitor_ips').document('10.0.10.1').set({'timestamp': one_day_ago})
    monkeypatch.setattr('cloud_resume.db.ip_cache', {})
    response = client.get('/', headers={"X-Forwarded-For": "10.0.10.1"})
    assert_counter_value(response, 3)

def test_counter_integration_stale_ip_cache_only_increments_once(setup_firestore_emulator, client, monkeypatch, mocker):
    """
    Tests the counter integration for stale ip_cache entries.

    This test checks that the visitor counter is only incremented once when the client IP is already
    present in ip_cache with an expired timestamp.
    """
    firestore_port = setup_firestore_emulator
    monkeypatch.setenv('FIRESTORE_EMULATOR_HOST', f'localhost:{firestore_port}')
    monkeypatch.setattr(db.database, "_db", None)

    client_ip = "10.0.10.2"
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=2)
    database = db.FirestoreClient()
    database.connect_to_firestore()

    database._db.collection('counters').document('visitor_count').set({'count': 10})
    database._db.collection('visitor_ips').document(client_ip).set({'timestamp': one_day_ago})
    monkeypatch.setattr('cloud_resume.db.ip_cache', {client_ip: one_day_ago})
    monkeypatch.setattr('cloud_resume.db.counter_cache', None)

    response = client.get('/', headers={"X-Forwarded-For": client_ip})
    assert_counter_value(response, 11)

    response = client.get('/', headers={"X-Forwarded-For": client_ip})
    assert_counter_value(response, 11)
