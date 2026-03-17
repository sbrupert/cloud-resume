import pytest
from datetime import datetime, timedelta, timezone
from cloud_resume.db import increment_counter, FirestoreClient
from cloud_resume import db

@pytest.mark.parametrize("cache_result, counter_cache, database_visitor_count, expected_result",[
    (True, 5, None, 5),             # Scenario 1: Cache hit, use cached counter.
    (True, None, None, 1),          # Scenario 2: Cache hit, no DB count, initialize to 1.
    (True, None, 27, 27),           # Scenario 3: Cache hit, DB count available, use DB count.
    (False, None, 10, 11),          # Scenario 4: Cache miss, increment DB count.
    (False, None, None, 1)          # Scenario 5: Cache miss, no DB count, initialize to 1.
], ids=[
    "cache_hit_use_cache_value",
    "cache_hit_initialize_count_to_1",
    "cache_hit_use_db_count",
    "cache_miss_increment_db_count",
    "cache_miss_initialize_count_to_1"
])

def test_increment_counter_cache(mocker, monkeypatch, cache_result, counter_cache, database_visitor_count, expected_result):
    """
    Tests the increment_counter() function for correct counter management.

    This test verifies if the function correctly manages the local counter cache and the database counter.
    It runs different scenarios to ensure the visitor counter is incremented correctly and that the cache is updated when necessary.
    Refer to the pytest parameterization section above for all test scenarios and their expected results.
    """
    monkeypatch.setattr("cloud_resume.db.counter_cache", counter_cache)
    mocker.patch('cloud_resume.db.cache_ip', return_value=cache_result)
    mocker.patch.object(FirestoreClient, "get_visitor_count", return_value = database_visitor_count)
    mocker.patch.object(FirestoreClient, "update_visitor_count", return_value = None)
    
    assert increment_counter() == expected_result


def test_increment_counter_exception(mocker, monkeypatch):
    """
    Tests the increment_counter() function for exception handling.

    This test checks whether the function handles exceptions and returns the appropriate "Unavailable" message.
    This message is what users see on the website if any errors occur during the incrementing process or within dependency functions.
    """
    monkeypatch.setattr("cloud_resume.db.counter_cache", None)
    mocker.patch('cloud_resume.db.cache_ip', side_effect=Exception("Mock DB error"))
    
    assert increment_counter() == "Unavailable"

def test_increment_counter_only_increments_once_for_expired_cached_ip(mocker, monkeypatch):
    client_ip = "192.168.1.1"
    current_time = datetime.now(timezone.utc)
    expired_time = current_time - timedelta(days=2)

    counter_state = {"count": 10}
    db_state = {client_ip: {"timestamp": expired_time}}

    def fake_update_visitor_ip(ip_address, timestamp):
        db_state[ip_address] = {"timestamp": timestamp}
        return True
    
    def fake_get_visitor_count():
        return counter_state["count"]
    
    def fake_update_visitor_count(count):
        counter_state["count"] = count
    
    mocker.patch("cloud_resume.db.get_client_ip", return_value=client_ip)
    
    mocker.patch.object(
        db.FirestoreClient,
        "update_visitor_ip",
        side_effect=fake_update_visitor_ip,
    )
    mock_get_visitor_count = mocker.patch.object(
        db.FirestoreClient,
        "get_visitor_count",
        side_effect=fake_get_visitor_count,
    )
    mock_update_visitor_count = mocker.patch.object(
        db.FirestoreClient,
        "update_visitor_count",
        side_effect=fake_update_visitor_count,
    )

    monkeypatch.setattr("cloud_resume.db.ip_cache", {client_ip: expired_time})
    monkeypatch.setattr("cloud_resume.db.counter_cache", None)

    first_result = db.increment_counter()
    second_result = db.increment_counter()

    assert first_result == 11
    assert second_result == 11
    mock_update_visitor_count.assert_called_once_with(11)  
