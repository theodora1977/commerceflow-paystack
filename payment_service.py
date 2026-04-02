import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)

def get_auth_headers():
    """
    Always returns fresh headers. This prevents issues where the 
    Secret Key might be empty during the initial module load.
    """
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY.get_secret_value()}",
        "Content-Type":  "application/json"
    }

# FUNCTION 1 — Initialize Payment

def initialize_payment(email: str, amount: int, reference: str):
    """
    Sends payment request to Paystack.

    Args:
        email     : customer's email address
        amount    : price in NAIRA
        reference : unique ID for this transaction

    Returns:
        dict: Paystack API response
    """
    url = f"{settings.PAYSTACK_BASE_URL}/transaction/initialize"

    # Use 127.0.0.1 to match your local server environment
    host_url = settings.APP_URL.rstrip("/")

    payload = {
        "email"     : email,
        "amount"    : amount * 100,   # Paystack needs KOBO → multiply by 100
        "reference" : reference,
        # Redirect user back to our success.html page
        "callback_url": f"{host_url}/success"
    }

    logger.info(f"Initializing Paystack payment for {email} — ₦{amount}")
    # Debug: Check the first few characters of the key being sent
    secret_preview = settings.PAYSTACK_SECRET_KEY.get_secret_value()[:7]
    logger.debug(f"Using Key starting with: {secret_preview}...")

    try:
        response = httpx.post(url, json=payload, headers=get_auth_headers(), timeout=10)
        result   = response.json()
        
        if not result.get("status"):
            logger.error(f"Paystack Error: {result.get('message')} | HTTP {response.status_code}")
            
        return result

    except Exception as e:
        logger.exception("Failed to initialize payment")
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

    url = f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}"

    logger.info(f"Verifying transaction reference: {reference}")

    try:
        response = httpx.get(url, headers=get_auth_headers(), timeout=10)
        result   = response.json()
        logger.info(f"Verify Result: {result.get('data', {}).get('status')}")
        return result

    except Exception as e:
        logger.exception(f"Verification failed for reference: {reference}")
        return {"status": False, "message": str(e)}