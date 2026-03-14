"""Tests for the Stripe payment integration endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.adapters.api.main import create_app
from src.config.settings import Settings


@pytest.fixture
def client():
    settings = Settings(
        database_url="sqlite+aiosqlite:///test.db",
        stripe_secret_key="sk_test_fake",
        stripe_webhook_secret="whsec_test_fake",
        stripe_price_id="price_test_123",
        frontend_url="http://localhost:3000",
    )
    app = create_app(settings)
    return TestClient(app)


@pytest.fixture
def client_no_stripe():
    settings = Settings(database_url="sqlite+aiosqlite:///test.db")
    app = create_app(settings)
    return TestClient(app)


def test_checkout_returns_503_when_stripe_not_configured(client_no_stripe):
    response = client_no_stripe.post(
        "/api/v1/payments/create-checkout-session",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_checkout_requires_email(client):
    response = client.post(
        "/api/v1/payments/create-checkout-session",
        json={},
    )
    assert response.status_code == 422


@patch("src.adapters.api.routers.payments.stripe")
def test_checkout_creates_session(mock_stripe, client):
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/session/test_123"
    mock_session.id = "cs_test_123"
    mock_stripe.checkout.Session.create.return_value = mock_session

    response = client.post(
        "/api/v1/payments/create-checkout-session",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["checkout_url"] == "https://checkout.stripe.com/session/test_123"
    assert data["session_id"] == "cs_test_123"


@patch("src.adapters.api.routers.payments.stripe")
def test_checkout_handles_stripe_error(mock_stripe, client):
    import stripe as stripe_mod

    mock_stripe.StripeError = stripe_mod.StripeError
    mock_stripe.checkout.Session.create.side_effect = stripe_mod.StripeError(
        "Card declined"
    )

    response = client.post(
        "/api/v1/payments/create-checkout-session",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 502


def test_webhook_returns_503_when_not_configured(client_no_stripe):
    response = client_no_stripe.post(
        "/api/v1/payments/webhook",
        content=b"{}",
        headers={"stripe-signature": "test_sig"},
    )
    assert response.status_code == 503


@patch("src.adapters.api.routers.payments.stripe")
def test_webhook_validates_signature(mock_stripe, client):
    import stripe as stripe_mod

    mock_stripe.SignatureVerificationError = stripe_mod.SignatureVerificationError
    mock_stripe.Webhook.construct_event.side_effect = (
        stripe_mod.SignatureVerificationError("bad sig", "header")
    )

    response = client.post(
        "/api/v1/payments/webhook",
        content=b'{"type": "test"}',
        headers={"stripe-signature": "bad_signature"},
    )
    assert response.status_code == 400


@patch("src.adapters.api.routers.payments.stripe")
def test_webhook_handles_checkout_completed(mock_stripe, client):
    mock_stripe.SignatureVerificationError = Exception
    mock_stripe.Webhook.construct_event.return_value = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer_email": "test@example.com",
                "customer": "cus_123",
                "subscription": "sub_123",
            }
        },
    }

    response = client.post(
        "/api/v1/payments/webhook",
        content=b'{"type": "checkout.session.completed"}',
        headers={"stripe-signature": "valid_sig"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("src.adapters.api.routers.payments.stripe")
def test_webhook_handles_subscription_deleted(mock_stripe, client):
    mock_stripe.SignatureVerificationError = Exception
    mock_stripe.Webhook.construct_event.return_value = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_123",
            }
        },
    }

    response = client.post(
        "/api/v1/payments/webhook",
        content=b'{"type": "customer.subscription.deleted"}',
        headers={"stripe-signature": "valid_sig"},
    )
    assert response.status_code == 200
