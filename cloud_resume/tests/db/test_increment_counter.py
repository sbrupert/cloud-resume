import pytest
from cloud_resume.db import increment_counter, FirestoreClient

@pytest.mark.parametrize("cache_result, counter_cache, database_visitor_count, expected_result",[
    (True, 5, None, 5),             # Scenario 1: Cache hit, use cached counter
    (True, None, None, 1),          # Scenario 2: Cache hit, no DB count, initialize to 1
    (True, None, 27, 27),           # Scenario 3: Cache hit, DB count available, use DB count
    (False, None, 10, 11),          # Scenario 4: Cache miss, increment DB count
    (False, None, None, 1)          # Scenario 5: Cache miss, no DB count, initialize to 1
], ids=[
    "cache_hit_use_cache_value",
    "cache_hit_initialize_count_to_1",
    "cache_hit_use_db_count",
    "cache_miss_increment_db_count",
    "cache_miss_initialize_count_to_1"
])

def test_increment_counter_cache(mocker, monkeypatch, cache_result, counter_cache, database_visitor_count, expected_result):
    monkeypatch.setattr("cloud_resume.db.counter_cache", counter_cache)
    mocker.patch('cloud_resume.db.cache_ip', return_value=cache_result)
    mocker.patch.object(FirestoreClient, "get_visitor_count", return_value = database_visitor_count)
    mocker.patch.object(FirestoreClient, "update_visitor_count", return_value = None)
    
    assert increment_counter() == expected_result


def test_increment_counter_exception(mocker, monkeypatch):
    monkeypatch.setattr("cloud_resume.db.counter_cache", None)
    mocker.patch('cloud_resume.db.cache_ip', side_effect=Exception("Mock DB error"))
    
    assert increment_counter() == "Unavailable"