from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from axiom_api.config import settings
from axiom_api.routers import audit, auth, events, fields, groups, tests


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(title="Axiom API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_public_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tests.router, prefix="/api/tests", tags=["tests"])
app.include_router(events.router, prefix="/api", tags=["events"])
app.include_router(fields.router, prefix="/api/metadata-fields", tags=["metadata-fields"])
app.include_router(groups.router, prefix="/api", tags=["groups"])
app.include_router(audit.router, prefix="/api/audit", tags=["audit"])
