import uvicorn
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import engine, Base
import models
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

# Mount the frontend directory to serve CSS, JS, and Images
# This allows you to link <link rel="stylesheet" href="/static/style.css"> in your HTML
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Include our modular routes
app.include_router(payment_router)
app.include_router(webhook_router)

@app.get("/")
def serve_frontend():
    """Serve the main index.html from the frontend directory."""
    return FileResponse("frontend/index.html")

@app.get("/success")
def serve_success():
    """Serve the success page after payment."""
    return FileResponse("frontend/success.html")

@app.get("/products/")
def get_products():
    """Read product catalog from products.json and assign IDs for the frontend."""
    try:
        with open("products.json", "r") as f:
            products = json.load(f)
        
        # Assign unique IDs so the cart logic works
        for i, item in enumerate(products):
            item["id"] = i + 1
            
        return products
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading products.json: {e}")
        return []

if __name__ == "__main__":
    # This allows running via 'python main.py' as well as uvicorn command
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)