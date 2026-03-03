import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimiter(BaseHTTPMiddleware):
    """
    In-memory sliding window rate limiter.
    Limits per IP address on AI-heavy endpoints.
    """

    def __init__(self, app, requests_per_minute: int = 10, requests_per_day: int = 200):
        super().__init__(app)
        self.rpm = requests_per_minute
        self.rpd = requests_per_day
        # { ip: [timestamp, ...] }
        self._minute_hits: dict[str, list[float]] = defaultdict(list)
        self._day_hits: dict[str, list[float]] = defaultdict(list)

    # Endpoints that cost AI credits
    RATE_LIMITED_PATHS = {"/api/search", "/api/rewrite", "/api/word-of-the-day"}

    def _get_client_ip(self, request: Request) -> str:
        # Check forwarded headers (Render, Vercel proxies)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"

    def _clean_old(self, hits: list[float], window: float) -> list[float]:
        now = time.time()
        return [t for t in hits if now - t < window]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Only rate-limit AI endpoints
        if path not in self.RATE_LIMITED_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        ip = self._get_client_ip(request)
        now = time.time()

        # Clean and check per-minute
        self._minute_hits[ip] = self._clean_old(self._minute_hits[ip], 60)
        if len(self._minute_hits[ip]) >= self.rpm:
            logger.warning(f"Rate limit (per-minute) hit by {ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Too many requests. Limit: {self.rpm}/minute. Please wait a moment.",
            )

        # Clean and check per-day
        self._day_hits[ip] = self._clean_old(self._day_hits[ip], 86400)
        if len(self._day_hits[ip]) >= self.rpd:
            logger.warning(f"Rate limit (per-day) hit by {ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit reached ({self.rpd} requests). Try again tomorrow.",
            )

        # Record hit
        self._minute_hits[ip].append(now)
        self._day_hits[ip].append(now)

        return await call_next(request)
