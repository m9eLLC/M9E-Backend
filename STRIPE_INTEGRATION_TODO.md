# Stripe Integration TODO

Hosted Stripe Checkout: customers are sent to a Stripe-hosted payment page. This file is the single source of truth for the remaining setup.

## Values to Replace

The following values are placeholders and must be updated before going live.

**Files containing placeholders:**
- [app/routers/checkout.py](app/routers/checkout.py)
- [app/config.py](app/config.py) (`checkout_domain` default)
- [.env.example](.env.example) (`CHECKOUT_DOMAIN`)

| Field | Current Value | What to Set |
|-------|--------------|-------------|
| mode | payment | Set to "payment" for one-time charges or "subscription" for recurring billing. If "subscription", `payment_method_collection: "always"` is added automatically. |
| success_url | `{CHECKOUT_DOMAIN}/success?session_id={CHECKOUT_SESSION_ID}` (CHECKOUT_DOMAIN defaults to https://example.com) | Set `CHECKOUT_DOMAIN` to the real site (e.g. the marketplace UI origin) and make sure a `/success` page exists there. Keep the `{CHECKOUT_SESSION_ID}` template. |
| cancel_url | `{CHECKOUT_DOMAIN}/cancel` | Your actual cancel/return page. |
| line_items[].price | price_... | Your actual Stripe Price ID from the Dashboard (https://dashboard.stripe.com/prices) or API. |

## Configured Parameters

These parameters were configured in Checkout Studio and are already set correctly.

**Files containing these parameters:**
- [app/routers/checkout.py](app/routers/checkout.py)

| Parameter | Value |
|-----------|-------|
| ui_mode | hosted_page |
| billing_address_collection | auto |
| phone_number_collection | { enabled: false } |
| automatic_tax | { enabled: false } |
| allow_promotion_codes | false |
| payment_method_collection | always (sent only when mode is "subscription") |
| submit_type | auto |
| integration_identifier | hosted_web_0001 |
| origin_context | web |

`ui_mode: "hosted_page"` was checked against the pinned Python SDK (`stripe==16.1.0`): its Checkout Session types list `hosted_page` and default to it. If you pin an older SDK, check whether it needs `hosted` instead.

## Setup

1. **Dependency** — `stripe==16.1.0` is in [requirements.txt](requirements.txt). Locally: `.venv/bin/pip install -r requirements.txt`.
2. **Environment variables** (server-side only, never in the front end):
   - `STRIPE_SECRET_KEY` — from https://dashboard.stripe.com/test/apikeys (use `sk_test_...` until live).
   - `CHECKOUT_DOMAIN` — site Checkout returns customers to.
   - Locally: add both to `.env`. On Render: enter them in the `m9e-backend` service's Environment tab (declared in [render.yaml](render.yaml)).
3. The Stripe API version is left at the SDK default (no version is pinned in code).

## New files and changes

```
app/routers/checkout.py     POST /v1/checkout/sessions (new)
app/main.py                 registers the checkout router
app/config.py               stripe_secret_key, checkout_domain settings
.env.example, render.yaml   STRIPE_SECRET_KEY, CHECKOUT_DOMAIN
requirements.txt            stripe==16.1.0
```

## How it works

1. The marketplace UI calls `POST /v1/checkout/sessions` with a Supabase bearer token, or the `X-Internal-Api-Key` header for server-to-server calls (same auth as `/v1/listings`).
2. The gateway creates a Checkout Session and returns `{ "id": "cs_...", "url": "https://checkout.stripe.com/..." }`.
3. The UI sends the browser to `url` (`window.location.href = url`).
4. Stripe takes payment and sends the customer to `success_url` (or `cancel_url` if they back out).
5. Without `STRIPE_SECRET_KEY` the endpoint returns 503; Stripe errors return 502.

## Testing

- Test card: `4242 4242 4242 4242`, any future expiry, any CVC, any postcode.
- Needs authentication (3DS): `4000 0025 0000 3155`. Declined: `4000 0000 0000 9995`.
- More: https://docs.stripe.com/testing. Use test-mode keys only until going live.

## Next steps

- Create the products and prices in the Dashboard, then replace `price_...` (or take the price/listing from the request body).
- **Fulfilment:** add a webhook endpoint for `checkout.session.completed` (verify signatures with a `STRIPE_WEBHOOK_SECRET` from https://dashboard.stripe.com/workbench/webhooks). No webhook exists yet. Do not rely on the success page for fulfilment.
- **Order tracking:** store the session ID, customer ID and payment status against the listing or order in Supabase once that model exists.
- Decide `mode` per product (one-time vs subscription).

## Resources

- https://support.stripe.com
- https://docs.stripe.com/mcp
