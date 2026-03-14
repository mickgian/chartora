"""Stripe payment integration for premium subscriptions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import stripe
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


def _get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def _init_stripe(settings: Settings) -> None:
    stripe.api_key = settings.stripe_secret_key


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
) -> dict[str, Any]:
    """Create a Stripe Checkout session for the premium subscription.

    The frontend redirects the user to the returned URL.
    """
    settings = _get_settings(request)
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Payments not configured")

    _init_stripe(settings)

    body = await request.json()
    customer_email: str | None = body.get("email")
    if not customer_email:
        raise HTTPException(status_code=422, detail="Email is required")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            customer_email=customer_email,
            line_items=[
                {
                    "price": settings.stripe_price_id,
                    "quantity": 1,
                }
            ],
            success_url=f"{settings.frontend_url}/pro?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/pro?canceled=true",
        )
    except stripe.StripeError as e:
        logger.exception("Stripe checkout error: %s", e)
        raise HTTPException(status_code=502, detail="Payment provider error") from e

    return {"checkout_url": session.url, "session_id": session.id}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
) -> JSONResponse:
    """Handle Stripe webhook events for subscription lifecycle."""
    settings = _get_settings(request)
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    _init_stripe(settings)
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.stripe_webhook_secret,
        )
    except stripe.SignatureVerificationError as e:
        logger.warning("Invalid Stripe signature: %s", e)
        raise HTTPException(status_code=400, detail="Invalid signature") from e
    except ValueError as e:
        logger.warning("Invalid Stripe payload: %s", e)
        raise HTTPException(status_code=400, detail="Invalid payload") from e

    event_type: str = event["type"]
    data_object: dict[str, Any] = event["data"]["object"]

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(data_object)
    elif event_type == "customer.subscription.updated":
        _handle_subscription_updated(data_object)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_deleted(data_object)
    elif event_type == "invoice.payment_failed":
        _handle_payment_failed(data_object)
    else:
        logger.info("Unhandled Stripe event: %s", event_type)

    return JSONResponse(content={"status": "ok"})


def _handle_checkout_completed(session: dict[str, Any]) -> None:
    customer_email = session.get("customer_email", "")
    customer_id = session.get("customer", "")
    subscription_id = session.get("subscription", "")
    logger.info(
        "checkout_completed email=%s customer=%s subscription=%s",
        customer_email,
        customer_id,
        subscription_id,
    )


def _handle_subscription_updated(subscription: dict[str, Any]) -> None:
    sub_id = subscription.get("id", "")
    status = subscription.get("status", "")
    logger.info("subscription_updated id=%s status=%s", sub_id, status)


def _handle_subscription_deleted(subscription: dict[str, Any]) -> None:
    sub_id = subscription.get("id", "")
    logger.info("subscription_deleted id=%s", sub_id)


def _handle_payment_failed(invoice: dict[str, Any]) -> None:
    customer = invoice.get("customer", "")
    logger.warning("payment_failed customer=%s", customer)
