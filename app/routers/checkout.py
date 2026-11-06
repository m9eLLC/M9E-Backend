from typing import Literal

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.config import settings
from app.deps import get_current_user_or_service

router = APIRouter(prefix="/v1/checkout", tags=["checkout"], dependencies=[Depends(get_current_user_or_service)])

# Fees sold through Checkout. Each maps to a Stripe Price ID set in the environment,
# and a mode: "payment" for one-time charges, "subscription" for recurring ones.
CATALOG = {
    "listing_fee": {"price_setting": "stripe_price_listing_fee", "mode": "payment"},
    "inspection_fee": {"price_setting": "stripe_price_inspection_fee", "mode": "payment"},
}


class CheckoutSessionRequest(BaseModel):
    item: Literal["listing_fee", "inspection_fee"]


@router.post("/sessions")
def create_checkout_session(body: CheckoutSessionRequest):
    """Creates a Stripe-hosted Checkout Session for one fee and returns its URL; the caller redirects the browser there."""
    entry = CATALOG[body.item]
    price_id = getattr(settings, entry["price_setting"])
    if not settings.stripe_secret_key or not price_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe is not configured")

    mode = entry["mode"]
    params = {
        # Configured in Checkout Studio.
        "ui_mode": "hosted_page",
        "billing_address_collection": "auto",
        "phone_number_collection": {"enabled": False},
        "automatic_tax": {"enabled": False},
        "allow_promotion_codes": False,
        "submit_type": "auto",
        "integration_identifier": "hosted_web_0001",
        "origin_context": "web",
        # See STRIPE_INTEGRATION_TODO.md.
        "mode": mode,
        "success_url": f"{settings.checkout_domain}/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{settings.checkout_domain}/cancel",
        "line_items": [{"price": price_id, "quantity": 1}],
    }
    if mode == "subscription":
        params["payment_method_collection"] = "always"

    try:
        session = stripe.checkout.Session.create(api_key=settings.stripe_secret_key, **params)
    except stripe.StripeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.user_message or "Stripe error")

    return {"id": session.id, "url": session.url}
