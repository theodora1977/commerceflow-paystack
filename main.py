import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from payment_routes import router as payment_router
from webhook import router as webhook_router
from config import settings

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

# IMPORTANT: Allow your frontend (likely running on a different port or file) to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include our modular routes
app.include_router(payment_router)
app.include_router(webhook_router)

@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": "CommerceFlow Paystack API is running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    # This allows running via 'python main.py' as well as uvicorn command
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)