import logging
import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from app.core.config import get_settings
from app.core.database import init_db
from app.api.routes import router

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Self-ping interval (13 minutes — Render sleeps after 15 min of inactivity)
KEEP_ALIVE_INTERVAL = 13 * 60


async def keep_alive():
    """Background task: pings own health endpoint to prevent Render cold starts."""
    # Determine our own URL
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not render_url:
        logger.info("⏭️ Keep-alive skipped (not on Render)")
        return

    health_url = f"{render_url}/health"
    logger.info(f"🏓 Keep-alive started: pinging {health_url} every {KEEP_ALIVE_INTERVAL}s")

    async with httpx.AsyncClient(timeout=10.0) as client:
        while True:
            await asyncio.sleep(KEEP_ALIVE_INTERVAL)
            try:
                r = await client.get(health_url)
                logger.info(f"🏓 Keep-alive ping: {r.status_code}")
            except Exception as e:
                logger.warning(f"🏓 Keep-alive ping failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and start keep-alive on startup."""
    logger.info("🚀 Starting Lexify API...")
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database init skipped: {e}")

    # Start keep-alive background task
    ping_task = asyncio.create_task(keep_alive())

    yield

    # Cleanup
    ping_task.cancel()
    logger.info("👋 Shutting down...")


app = FastAPI(
    title="Lexify API",
    description="AI-powered contextual word suggestion engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "https://lexify.harshjsx.dev",
    settings.FRONTEND_URL,
]
origins = list(set(o for o in origins if o))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Error Handlers (always include CORS headers) ──

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    origin = request.headers.get("origin", "*")
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Please try again."},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        },
    )


# Routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Lexify API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

