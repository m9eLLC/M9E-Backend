import stripe
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.deps import get_current_user_or_service

router = APIRouter(prefix="/v1/checkout", tags=["checkout"], dependencies=[Depends(get_current_user_or_service)])


@router.post("/sessions")
def create_checkout_session():
    """Creates a Stripe-hosted Checkout Session and returns its URL; the caller redirects the browser there."""
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe is not configured")

    # TODO: set to "subscription" if selling recurring products.
    mode = "payment"

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
        # Placeholders: see STRIPE_INTEGRATION_TODO.md.
        "mode": mode,
        "success_url": f"{settings.checkout_domain}/success?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{settings.checkout_domain}/cancel",
        "line_items": [{"price": "price_...", "quantity": 1}],
    }
    if mode == "subscription":
        params["payment_method_collection"] = "always"

    try:
        session = stripe.checkout.Session.create(api_key=settings.stripe_secret_key, **params)
    except stripe.StripeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=e.user_message or "Stripe error")

    return {"id": session.id, "url": session.url}
