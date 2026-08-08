from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import tickets, health

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
