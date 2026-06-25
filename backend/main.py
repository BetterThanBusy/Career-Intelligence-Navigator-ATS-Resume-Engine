"""
Career Intelligence Navigator — FastAPI Backend
Entry point: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from api.routes import ats, career, user, webhooks
from db.connection import init_db

log = structlog.get_logger()

app = FastAPI(
    title="Career Intelligence Navigator API",
    description="AI-powered career intelligence: ATS scoring + skill gap analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─────────────────────────────────────────
# CORS
# ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://career-intelligence.vercel.app",
        # Add your production domain here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────
app.include_router(ats.router, prefix="/api/ats", tags=["ATS"])
app.include_router(career.router, prefix="/api/career", tags=["Career Intelligence"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])


# ─────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ─────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await init_db()
    log.info("Career Intelligence Navigator API started")


# ─────────────────────────────────────────
# GLOBAL ERROR HANDLER
# ─────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error("Unhandled exception", error=str(exc), path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )
