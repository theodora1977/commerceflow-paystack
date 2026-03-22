import os
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# CONFIG
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_BASE_URL   = "https://api.paystack.co"

HEADERS = {
    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    "Content-Type":  "application/json"
}

# FUNCTION 1 — Initialize Payment

def initialize_payment(email: str, amount: int, reference: str):
    """
    Sends payment request to Paystack.

    Args:
        email     : customer's email address
        amount    : price in NAIRA (we convert to kobo inside)
        reference : unique ID for this transaction

    Returns:
        dict: Paystack API response
    """

    url = f"{PAYSTACK_BASE_URL}/transaction/initialize"

    payload = {
        "email"     : email,
        "amount"    : amount * 100,   # Paystack needs KOBO → multiply by 100
        "reference" : reference,
        "callback_url": os.getenv("BASE_URL", "http://localhost:8000") + "/payment/verify"
    }

    print(f"[INIT PAYMENT] Sending request for {email}, amount: ₦{amount}")

    try:
        response = httpx.post(url, json=payload, headers=HEADERS, timeout=10)
        result   = response.json()
        print(f"[INIT PAYMENT] Response: {result}")
        return result

    except Exception as e:
        print(f"[INIT PAYMENT ERROR] {str(e)}")
        return {"status": False, "message": str(e)}


# FUNCTION 2 — Verify Payment

def verify_payment(reference: str):
    """
    Checks with Paystack if a transaction was successful.

    Args:
        reference : the unique transaction reference to verify

    Returns:
        dict: Paystack API response
    """

    url = f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}"

    print(f"[VERIFY PAYMENT] Checking reference: {reference}")

    try:
        response = httpx.get(url, headers=HEADERS, timeout=10)
        result   = response.json()
        print(f"[VERIFY PAYMENT] Status: {result.get('data', {}).get('status')}")
        return result

    except Exception as e:
        print(f"[VERIFY PAYMENT ERROR] {str(e)}")
        return {"status": False, "message": str(e)}