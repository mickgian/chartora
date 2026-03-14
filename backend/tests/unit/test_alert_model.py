"""Tests for AlertPreference and ApiKey domain entities."""

from src.domain.models.entities import AlertPreference, ApiKey


def test_alert_preference_creation():
    alert = AlertPreference(
        user_id=1,
        alert_type="score_change",
        enabled=True,
        threshold=10.0,
    )
    assert alert.user_id == 1
    assert alert.alert_type == "score_change"
    assert alert.enabled is True
    assert alert.threshold == 10.0


def test_alert_preference_defaults():
    alert = AlertPreference(user_id=1, alert_type="insider_trading")
    assert alert.enabled is True
    assert alert.threshold is None
    assert alert.id is None


def test_api_key_creation():
    key = ApiKey(
        user_id=1,
        key_hash="abc123hash",
        name="My Key",
        prefix="ck_abc123",
    )
    assert key.user_id == 1
    assert key.key_hash == "abc123hash"
    assert key.name == "My Key"
    assert key.prefix == "ck_abc123"
    assert key.is_active is True


def test_api_key_defaults():
    key = ApiKey(
        user_id=1,
        key_hash="hash",
        name="Default",
        prefix="ck_test",
    )
    assert key.created_at is None
    assert key.last_used_at is None
    assert key.is_active is True
    assert key.id is None
