from datetime import datetime, timedelta, timezone
import cloud_resume.db as db

def test_cache_ip_updates_firestore_when_local_cache_entry_is_expired(
    mocker, monkeypatch
):
    """
    If the client IP is found in the local ip_cache but the cached timestamp is
    older than 24 hours, the app should refresh the timestamp in Firestore and
    refresh the local cache entry.
    """
    client_ip = "192.168.1.1"
    current_time = datetime.now(timezone.utc)
    expired_time = current_time - timedelta(days=2)
    db_state = { client_ip: {"timestamp": expired_time}}
    
    def fake_update_visitor_ip(ip_address, timestamp):
        db_state[ip_address] = {"timestamp": timestamp}
        return True

    mock_update_visitor_ip = mocker.patch.object(
        db.FirestoreClient,
        "update_visitor_ip",
        side_effect=fake_update_visitor_ip,
    )

    mocker.patch("cloud_resume.db.get_client_ip", return_value=client_ip)

    monkeypatch.setattr(
        "cloud_resume.db.ip_cache",
        {client_ip: expired_time},
    )

    result = db.cache_ip()

    # cache_ip() should return False on expired cache items.
    assert result is False

    # Firestore should be updated with the new timestamp for the expired IP.
    mock_update_visitor_ip.assert_called_once_with(client_ip, db.ip_cache[client_ip])

    # Firestore should have timestamp updated and equal to the cache's value.
    assert db_state[client_ip]["timestamp"] > expired_time
    assert db.ip_cache[client_ip] == db_state[client_ip]["timestamp"]
