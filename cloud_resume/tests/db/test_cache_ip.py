import pytest
from datetime import datetime, timezone, timedelta
from cloud_resume.db import cache_ip, FirestoreClient

# Define the current time and a time exactly one day ago
current_time = datetime.now(timezone.utc)
one_day_ago = current_time - timedelta(days=1)

# Parameterize the test with various scenarios
@pytest.mark.parametrize(
    "ip_cache_content, db_content, db_exists, expected_result", [
        ({"192.168.1.1": current_time}, {"timestamp": current_time}, True, True), # Scenario 1: client_ip in ip_cache, timestamp not expired. Return True
        ({"192.168.1.1": one_day_ago}, {"timestamp": one_day_ago}, True, False),  # Scenario 2: client_ip in ip_cache, timestamp expired. Return False
        ({}, {"timestamp": current_time}, True, True),                            # Scenario 3: client_ip not in ip_cache, client_ip in db, timestamp not expired. Return True
        ({}, {"timestamp": one_day_ago}, True, False),                            # Scenario 4: client_ip not in ip_cache, client_ip in db, timestamp expired. Return False
        ({}, None, False, False),                                                 # Scenario 5: client_ip not in ip_cache, client_ip not in db. Return False
    ], ids= [
        "not_expired_in_cache",
        "expired_in_cache",
        "not_expired_in_db",
        "expired_in_db",
        "not_in_db"
])

def test_cache_ip(mocker, monkeypatch, ip_cache_content, db_content, db_exists, expected_result):
    """
    Tests the cache_ip() function for the proper return values.

    This test checks to see if the cache_ip() function returns the correct return value in certain sceanrios.
    Generally speaking, if the timestamp of a client IP is expired in either the cache or db, the function should return False.
    Otherwise, it should return True.
    """
    # Mock the IP retrieval functions and set up cache/db contents
    mocker.patch("cloud_resume.db.get_client_ip", return_value="192.168.1.1")
    mocker.patch.object(FirestoreClient, "get_visitor_ip", return_value=(db_exists, db_content))
    mocker.patch.object(FirestoreClient, "update_visitor_ip", return_value=True)
    monkeypatch.setattr("cloud_resume.db.ip_cache", ip_cache_content)

    # Assert the result of cache_ip
    assert cache_ip() == expected_result
