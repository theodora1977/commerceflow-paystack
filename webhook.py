from fastapi import APIRouter, Request, Header, HTTPException
import hmac
import hashlib
import os
import json

router = APIRouter()

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET_KEY", "sk_test_xxx")


# -----------------------------
# VERIFY PAYSTACK SIGNATURE
# -----------------------------
def verify_signature(request_body: bytes, signature: str):
    computed_hash = hmac.new(
        PAYSTACK_SECRET.encode("utf-8"),
        request_body,
        hashlib.sha512
    ).hexdigest()

    return computed_hash == signature


# -----------------------------
# WEBHOOK ENDPOINT
# -----------------------------
@router.post("/webhook/paystack")
async def paystack_webhook(
    request: Request,
    x_paystack_signature: str = Header(None)
):
    body = await request.body()

    # 🔐 Verify request is from Paystack
    if not verify_signature(body, x_paystack_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    event = json.loads(body)

    # -----------------------------
    # HANDLE EVENTS
    # -----------------------------
    if event["event"] == "charge.success":
        data = event["data"]

        reference = data["reference"]
        amount = data["amount"]
        email = data["customer"]["email"]

        print("✅ Payment Successful!")
        print(f"Reference: {reference}")
        print(f"Amount: {amount}")
        print(f"Email: {email}")

        # TODO: Update database here
        # Example:
        # update_order_status(reference, "paid")

    return {"status": "success"}