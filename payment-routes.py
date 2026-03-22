import uuid
from fastapi          import APIRouter, HTTPException
from pydantic         import BaseModel
from payment_service  import initialize_payment, verify_payment


# ROUTER SETUP

router = APIRouter(
    prefix="/payment",   # all routes start with /payment
    tags=["Payment"]     # groups them in /docs
)

# REQUEST BODY SHAPE

class PaymentRequest(BaseModel):
    email  : str
    amount : int   # in Naira — no kobo needed from frontend

# ROUTE 1 — Start a Payment
# POST /payment/initialize

@router.post("/initialize")
def start_payment(data: PaymentRequest):
    """
    Frontend calls this to begin checkout.
    Returns a Paystack payment link for the user.
    """

    # Generate a unique reference for this transaction
    reference = str(uuid.uuid4())

    print(f"[ROUTE] /initialize called — email: {data.email}, amount: ₦{data.amount}")

    # Call the service function
    result = initialize_payment(data.email, data.amount, reference)

    # If Paystack returned an error
    if not result.get("status"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Payment initialization failed")
        )

    # Return the payment link and reference to frontend
    return {
        "message"           : "Payment initialized successfully",
        "authorization_url" : result["data"]["authorization_url"],  # redirect user here
        "reference"         : reference
    }


# ROUTE 2 — Verify a Payment
# GET /payment/verify?reference=xxx

@router.get("/verify")
def confirm_payment(reference: str):
    """
    Called after user pays — checks if payment was successful.
    Paystack redirects here automatically via callback_url.
    """

    print(f"[ROUTE] /verify called — reference: {reference}")

    # Call service function
    result = verify_payment(reference)

    # If Paystack returned an error
    if not result.get("status"):
        raise HTTPException(
            status_code=400,
            detail="Could not verify payment. Try again."
        )

    # Pull out the important info
    payment_data   = result["data"]
    payment_status = payment_data["status"]   # "success", "failed", "abandoned"
    amount_naira   = payment_data["amount"] / 100   # convert kobo back to Naira

    return {
        "message"   : f"Payment {payment_status}",
        "status"    : payment_status,
        "reference" : reference,
        "amount"    : f"₦{amount_naira}",
        "email"     : payment_data["customer"]["email"]
    }