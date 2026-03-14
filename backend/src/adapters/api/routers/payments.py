"""Stripe payment integration for premium subscriptions."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import stripe
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import JSONResponse

from src.domain.models.entities import User
from src.domain.models.value_objects import SubscriptionStatus

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

    factory = getattr(request.app.state, "session_factory", None)
    if factory is None:
        logger.error("No DB session factory — cannot process webhook")
        return JSONResponse(content={"status": "ok"})

    async with factory() as session:
        from src.adapters.repositories import PgUserRepository

        user_repo = PgUserRepository(session)

        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(data_object, user_repo)
        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(data_object, user_repo)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(data_object, user_repo)
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(data_object, user_repo)
        else:
            logger.info("Unhandled Stripe event: %s", event_type)

        await session.commit()

    return JSONResponse(content={"status": "ok"})


async def _handle_checkout_completed(
    session_data: dict[str, Any],
    user_repo: Any,
) -> None:
    customer_email = session_data.get("customer_email", "")
    customer_id = session_data.get("customer", "")
    subscription_id = session_data.get("subscription", "")
    logger.info(
        "checkout_completed email=%s customer=%s subscription=%s",
        customer_email,
        customer_id,
        subscription_id,
    )

    if not customer_email:
        return

    user = await user_repo.get_by_email(customer_email)
    if user is not None:
        # Update existing user with Stripe info
        user.stripe_customer_id = customer_id
        user.stripe_subscription_id = subscription_id
        user.subscription_status = SubscriptionStatus.ACTIVE
        await user_repo.update(user)
    else:
        # Create user record from Stripe checkout (no password — they can set via reset)
        from src.infrastructure.auth import hash_password

        new_user = User(
            email=customer_email,
            password_hash=hash_password(customer_email),  # placeholder
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            subscription_status=SubscriptionStatus.ACTIVE,
        )
        await user_repo.save(new_user)


async def _handle_subscription_updated(
    subscription: dict[str, Any],
    user_repo: Any,
) -> None:
    sub_id = subscription.get("id", "")
    status = subscription.get("status", "")
    logger.info("subscription_updated id=%s status=%s", sub_id, status)

    if not sub_id:
        return

    user = await user_repo.get_by_stripe_subscription_id(sub_id)
    if user is None:
        logger.warning("No user found for subscription %s", sub_id)
        return

    status_map = {
        "active": SubscriptionStatus.ACTIVE,
        "past_due": SubscriptionStatus.PAST_DUE,
        "canceled": SubscriptionStatus.CANCELED,
        "unpaid": SubscriptionStatus.PAST_DUE,
    }
    user.subscription_status = status_map.get(status, SubscriptionStatus.INACTIVE)
    await user_repo.update(user)


async def _handle_subscription_deleted(
    subscription: dict[str, Any],
    user_repo: Any,
) -> None:
    sub_id = subscription.get("id", "")
    logger.info("subscription_deleted id=%s", sub_id)

    if not sub_id:
        return

    user = await user_repo.get_by_stripe_subscription_id(sub_id)
    if user is None:
        return

    user.subscription_status = SubscriptionStatus.CANCELED
    await user_repo.update(user)


async def _handle_payment_failed(
    invoice: dict[str, Any],
    user_repo: Any,
) -> None:
    customer = invoice.get("customer", "")
    logger.warning("payment_failed customer=%s", customer)

    if not customer:
        return

    user = await user_repo.get_by_stripe_customer_id(customer)
    if user is None:
        return

    user.subscription_status = SubscriptionStatus.PAST_DUE
    await user_repo.update(user)
