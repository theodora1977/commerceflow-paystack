import uuid
import logging

from fastapi          import APIRouter, HTTPException, Depends
from sqlalchemy.orm   import Session

from database         import get_db
from models           import Order
from schemas          import PaymentInitRequest, PaymentInitResponse, PaymentVerifyResponse, OrderOut
# Ensure this matches your file name: payment_service.py
from payment_service import initialize_payment, verify_payment

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/payment",
    tags=["Payment"]
)


# =========================
# ROUTE 1 — Initialize Payment
# POST /payment/initialize
# =========================
@router.post("/initialize", response_model=PaymentInitResponse)
def start_payment(data: PaymentInitRequest, db: Session = Depends(get_db)):
    """
    Frontend calls this when the user clicks 'Buy Now'.
    1. Generates a unique reference
    2. Creates a pending Order record in the DB
    3. Calls Paystack to get the payment URL
    4. Returns the payment URL to the frontend
    """

    reference = str(uuid.uuid4())   # unique ID for this transaction

    logger.info(f"Initializing payment for {data.email}, amount: ₦{data.amount}")

    # =========================
    # STEP 1 — Save pending order BEFORE calling Paystack
    # This ensures we never lose a transaction reference even if Paystack is slow
    # =========================
    order = Order(
        email      = data.email,
        amount     = data.amount,
        reference  = reference,
        status     = "pending",
        product_id = data.product_id
    )
    db.add(order)
    db.commit()
    db.refresh(order)   # populate the auto-generated id

    logger.info(f"Order {order.id} created with status=pending")

    # =========================
    # STEP 2 — Call Paystack
    # =========================
    result = initialize_payment(data.email, data.amount, reference)

    if not result.get("status"):
        # Paystack rejected — update the order to 'failed' so we don't have ghost pending rows
        order.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Payment initialization failed")
        )

    return {
        "message"           : "Payment initialized successfully",
        "authorization_url" : result["data"]["authorization_url"],
        "reference"         : reference
    }


# =========================
# ROUTE 2 — Verify Payment
# GET /payment/verify?reference=xxx
# =========================
@router.get("/verify", response_model=PaymentVerifyResponse)
def confirm_payment(reference: str, db: Session = Depends(get_db)):
    """
    Paystack redirects the user here after they complete payment.
    1. Calls Paystack to get the real transaction status
    2. Updates the Order record in our DB
    3. Returns the result to the frontend
    """

    logger.info(f"Verifying payment for reference: {reference}")

    # =========================
    # STEP 1 — Ask Paystack for the real status
    # =========================
    result = verify_payment(reference)

    if not result.get("status"):
        raise HTTPException(status_code=400, detail="Could not verify payment. Try again.")

    payment_data   = result["data"]
    payment_status = payment_data["status"]          # "success", "failed", "abandoned"
    amount_naira   = float(payment_data["amount"]) / 100    # Ensure float for division

    # =========================
    # STEP 2 — Update the order status in our DB
    # =========================
    order = db.query(Order).filter(Order.reference == reference).first()

    if order:
        order.status = payment_status
        db.commit()
        logger.info(f"Order {reference} updated to status={payment_status}")
    else:
        # Edge case: user may have bypassed the initialize step
        logger.warning(f"No order found in DB for reference: {reference}")

    return {
        "message"   : f"Payment {payment_status}",
        "status"    : payment_status,
        "reference" : reference,
        "amount"    : f"₦{amount_naira}",
        "email"     : payment_data["customer"]["email"]
    }


# =========================
# ROUTE 3 — Get Order by Reference
# GET /payment/order/{reference}
# =========================
@router.get("/order/{reference}", response_model=OrderOut)
def get_order(reference: str, db: Session = Depends(get_db)):
    """
    Fetch a stored order record by its reference string.
    Useful for the frontend to poll order status after payment.
    """

    order = db.query(Order).filter(Order.reference == reference).first()

    if not order:
        raise HTTPException(status_code=404, detail=f"Order not found: {reference}")

    return order
