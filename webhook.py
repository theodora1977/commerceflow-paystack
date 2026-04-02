import hashlib
import hmac
import json

from fastapi             import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm      import Session

from config              import settings
from database            import get_db
from models              import Order


router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"]
)


# =========================
# ROUTE — Paystack Webhook
# POST /webhook/paystack
# =========================
@router.post("/paystack")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Paystack calls this URL automatically when a transaction event occurs.
    This is server-to-server — the user never sees this endpoint.

    Security model:
    - Paystack signs every webhook payload with HMAC-SHA512 using your secret key.
    - We recompute the hash on our side and compare.
    - If hashes don't match → reject immediately (could be a spoofed request).

    Events we handle:
        charge.success  → payment completed successfully
        charge.failed   → payment failed or declined
    """

    # Read the raw request body as bytes — must be raw for correct HMAC computation
    # If we parsed it as JSON first, byte ordering could differ and hash would fail
    body_bytes = await request.body()

    # Pull the signature Paystack injected into the request headers
    paystack_signature = request.headers.get("x-paystack-signature")

    # =========================
    # STEP 1 — Verify Signature
    # =========================
    if not _verify_signature(body_bytes, paystack_signature):
        print("[WEBHOOK] Signature verification FAILED — rejecting request")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    print("[WEBHOOK] Signature verified ✓")

    # =========================
    # STEP 2 — Parse Event
    # =========================
    try:
        payload = json.loads(body_bytes)   # safe to parse now that we've verified authenticity
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event     = payload.get("event")      # e.g. "charge.success"
    data      = payload.get("data", {})   # transaction details
    reference = data.get("reference")     # our UUID

    print(f"[WEBHOOK] Event received: {event} | Reference: {reference}")

    # =========================
    # STEP 3 — Handle Events
    # =========================

    if event == "charge.success":
        _handle_success(reference, db)

    elif event == "charge.failed":
        _handle_failure(reference, db)

    else:
        # Unknown event — log it but don't crash
        # Paystack sends many event types; we only care about charge events for now
        print(f"[WEBHOOK] Unhandled event type: {event} — ignoring")

    # Always return 200 to Paystack — if we return anything else,
    # Paystack will retry the webhook repeatedly (up to 5 times)
    return {"status": "received"}


# =========================
# HELPERS
# =========================

def _verify_signature(body: bytes, signature: str | None) -> bool:
    """
    Recomputes HMAC-SHA512 of the raw body using our Paystack secret key.
    Compares it against the signature Paystack sent.

    hmac.compare_digest is used instead of == to prevent timing attacks —
    a constant-time comparison so attackers can't brute-force the key
    by measuring how long the comparison takes.
    """
    if not signature:
        return False

    computed = hmac.new(
        settings.PAYSTACK_SECRET_KEY.get_secret_value().encode("utf-8"),
        body,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(computed, signature)


def _handle_success(reference: str, db: Session):
    """
    Marks the order as 'success' in the database.
    """
    order = db.query(Order).filter(Order.reference == reference).first()

    if not order:
        print(f"[WEBHOOK] No order found for reference: {reference}")
        return

    order.status = "success"
    db.commit()
    print(f"[WEBHOOK] Order {reference} marked as SUCCESS")


def _handle_failure(reference: str, db: Session):
    """
    Marks the order as 'failed' in the database.
    """
    order = db.query(Order).filter(Order.reference == reference).first()

    if not order:
        print(f"[WEBHOOK] No order found for reference: {reference}")
        return

    order.status = "failed"
    db.commit()
    print(f"[WEBHOOK] Order {reference} marked as FAILED")
