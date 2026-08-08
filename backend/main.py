import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import tickets, health

# Load OPENROUTER_API_KEY from backend/.env or root .env (local dev)
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

app = FastAPI(title="Resolve.AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tickets.router, prefix="/api")

@app.get("/")
def root():
    return {"service": "Resolve.AI", "docs": "/docs"}
