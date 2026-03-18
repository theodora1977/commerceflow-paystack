from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes (we will create these files next)
from product_routes import router as product_router
from payment_routes import router as payment_router
from webhook import router as webhook_router

app = FastAPI(title="CommerceFlow Paystack API")

# -----------------------------
# CORS CONFIG (VERY IMPORTANT)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later you can restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# INCLUDE ROUTES
# -----------------------------
app.include_router(product_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(webhook_router, prefix="/api")

# -----------------------------
# ROOT ENDPOINT
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "CommerceFlow Paystack Backend Running 🚀"
    }