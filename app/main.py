from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, intel, listings, quotes, search

app = FastAPI(title="M9E Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(listings.router)
app.include_router(search.router)
app.include_router(quotes.router)
app.include_router(intel.router)
