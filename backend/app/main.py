import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.core.database import init_db
from app.api.routes import router

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("🚀 Starting Better Word For API...")
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️ Database init skipped (will work without DB): {e}")
    yield
    logger.info("👋 Shutting down...")


app = FastAPI(
    title="Better Word For API",
    description="AI-powered contextual word suggestion engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — be explicit about origins to avoid credential conflicts
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler to ensure CORS headers on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    # Manually add CORS headers to ensure the browser doesn't block the error info
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)[:300]},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
    )


# FastAPI HTTPException handler
from fastapi import HTTPException
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
    )


# Routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Better Word For API", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

