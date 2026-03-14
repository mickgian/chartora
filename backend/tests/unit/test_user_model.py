"""Tests for the User domain entity."""

import pytest

from src.domain.models.entities import User
from src.domain.models.value_objects import SubscriptionStatus


def test_user_creation():
    user = User(email="test@example.com")
    assert user.email == "test@example.com"
    assert user.subscription_status == SubscriptionStatus.INACTIVE
    assert user.is_premium is False


def test_user_premium_active():
    user = User(
        email="premium@example.com",
        subscription_status=SubscriptionStatus.ACTIVE,
        stripe_customer_id="cus_123",
        stripe_subscription_id="sub_123",
    )
    assert user.is_premium is True


def test_user_premium_canceled():
    user = User(
        email="canceled@example.com",
        subscription_status=SubscriptionStatus.CANCELED,
    )
    assert user.is_premium is False


def test_user_premium_past_due():
    user = User(
        email="late@example.com",
        subscription_status=SubscriptionStatus.PAST_DUE,
    )
    assert user.is_premium is False


def test_user_invalid_email():
    with pytest.raises(ValueError, match="valid email"):
        User(email="invalid")


def test_user_empty_email():
    with pytest.raises(ValueError, match="valid email"):
        User(email="")
