# Stripe Integration TODO

Hosted Stripe Checkout: customers are sent to a Stripe-hosted payment page. This file is the single source of truth for the remaining setup.

## Values to Replace

The following values are placeholders and must be updated before going live.

**Files containing placeholders:**
- [app/routers/checkout.py](app/routers/checkout.py)
- [app/config.py](app/config.py) (`checkout_domain` default, empty price IDs)
- [.env.example](.env.example) (`CHECKOUT_DOMAIN`)

| Field | Current Value | What to Set |
|-------|--------------|-------------|
| line_items[].price (listing fee) | `STRIPE_PRICE_LISTING_FEE` (empty) | Price ID (`price_...`) of a one-time "Listing fee" price in the Dashboard (https://dashboard.stripe.com/products). |
| line_items[].price (inspection fee) | `STRIPE_PRICE_INSPECTION_FEE` (empty) | Price ID of a one-time "Inspection fee" price. |
| mode | payment (both fees, in `CATALOG`) | Keep "payment" for one-time fees. Change an entry to "subscription" only if that fee becomes recurring; `payment_method_collection: "always"` is then added automatically. |
| success_url | `{CHECKOUT_DOMAIN}/success?session_id={CHECKOUT_SESSION_ID}` (CHECKOUT_DOMAIN defaults to https://example.com) | Set `CHECKOUT_DOMAIN` to the real site (e.g. the marketplace UI origin) and make sure a `/success` page exists there. Keep the `{CHECKOUT_SESSION_ID}` template. |
| cancel_url | `{CHECKOUT_DOMAIN}/cancel` | Your actual cancel/return page. |

Until `STRIPE_SECRET_KEY` and the fee's price ID are both set, the endpoint returns 503 for that fee.

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
2. **Create the two products** in the Dashboard (Test mode): https://dashboard.stripe.com/products → **Add product**.
   - "Listing fee": one-off price, your amount and currency. Copy its price ID (`price_...`).
   - "Inspection fee": the same.
3. **Environment variables** (server-side only, never in the front end):
   - `STRIPE_SECRET_KEY` — from https://dashboard.stripe.com/test/apikeys (use `sk_test_...` until live). Secret: enter it yourself.
   - `STRIPE_PRICE_LISTING_FEE`, `STRIPE_PRICE_INSPECTION_FEE` — the two price IDs (not secret).
   - `CHECKOUT_DOMAIN` — site Checkout returns customers to.
   - Locally: add them to `.env`. On Render: enter them in the `m9e-backend` service's Environment tab (declared in [render.yaml](render.yaml)).
4. The Stripe API version is left at the SDK default (no version is pinned in code).

## New files and changes

```
app/routers/checkout.py     POST /v1/checkout/sessions (new)
app/main.py                 registers the checkout router
app/config.py               stripe_secret_key, checkout_domain settings
.env.example, render.yaml   STRIPE_SECRET_KEY, CHECKOUT_DOMAIN
requirements.txt            stripe==16.1.0
```

## How it works

1. The marketplace UI calls `POST /v1/checkout/sessions` with body `{"item": "listing_fee"}` or `{"item": "inspection_fee"}`, plus a Supabase bearer token or the `X-Internal-Api-Key` header for server-to-server calls (same auth as `/v1/listings`). Any other item returns 422.
2. The gateway creates a Checkout Session and returns `{ "id": "cs_...", "url": "https://checkout.stripe.com/..." }`.
3. The UI sends the browser to `url` (`window.location.href = url`).
4. Stripe takes payment and sends the customer to `success_url` (or `cancel_url` if they back out).
5. Without `STRIPE_SECRET_KEY` the endpoint returns 503; Stripe errors return 502.

## Testing

- Test card: `4242 4242 4242 4242`, any future expiry, any CVC, any postcode.
- Needs authentication (3DS): `4000 0025 0000 3155`. Declined: `4000 0000 0000 9995`.
- More: https://docs.stripe.com/testing. Use test-mode keys only until going live.

## Next steps

- To add another fee: add an entry to `CATALOG` in `app/routers/checkout.py`, a matching setting in `app/config.py`, and its `STRIPE_PRICE_...` variable.
- Link each payment to its listing (e.g. pass the listing ID as session `metadata`) once fulfilment is built.
- **Fulfilment:** add a webhook endpoint for `checkout.session.completed` (verify signatures with a `STRIPE_WEBHOOK_SECRET` from https://dashboard.stripe.com/workbench/webhooks). No webhook exists yet. Do not rely on the success page for fulfilment.
- **Order tracking:** store the session ID, customer ID and payment status against the listing or order in Supabase once that model exists.

## Resources

- https://support.stripe.com
- https://docs.stripe.com/mcp
