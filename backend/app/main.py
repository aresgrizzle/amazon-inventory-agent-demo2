from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.agent import router as agent_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.inventory import router as inventory_router
from backend.app.api.tasks import router as tasks_router
from backend.app.core.config import CORS_ALLOW_ORIGINS


app = FastAPI(title="Amazon Inventory Agent API")

allowed_origins = [
    origin.strip()
    for origin in CORS_ALLOW_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials="*" not in allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router)
app.include_router(inventory_router)
app.include_router(tasks_router)
app.include_router(agent_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Amazon Inventory Agent API is running"}
