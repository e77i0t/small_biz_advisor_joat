import os
import re
import hmac
import hashlib
import base64
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import aioredis

# --- Input Sanitization ---
def sanitize_string(value: str, max_length: int = 255) -> str:
    value = value.strip()
    value = re.sub(r'[<>"\']', '', value)  # Remove potentially dangerous chars
    return value[:max_length]

# --- Rate Limiting Middleware (Redis) ---
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_url: str, limit: int = 60, window: int = 60):
        super().__init__(app)
        self.redis_url = redis_url
        self.limit = limit
        self.window = window
        self.redis = None

    async def dispatch(self, request: Request, call_next: Callable):
        if self.redis is None:
            self.redis = await aioredis.from_url(self.redis_url)
        client_ip = getattr(request.client, 'host', 'unknown')
        key = f"ratelimit:{client_ip}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, self.window)
        if count > self.limit:
            return Response("Too Many Requests", status_code=429)
        return await call_next(request)

# --- API Key Authentication Middleware ---
class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, valid_api_keys: set):
        super().__init__(app)
        self.valid_api_keys = valid_api_keys

    async def dispatch(self, request: Request, call_next: Callable):
        api_key = request.headers.get("x-api-key")
        if not api_key or api_key not in self.valid_api_keys:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
        return await call_next(request)

# --- Security Headers Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

# --- Twilio Signature Validation ---
async def validate_twilio_signature(request: Request, auth_token: str) -> bool:
    signature = request.headers.get("X-Twilio-Signature")
    if not signature:
        return False
    url = str(request.url)
    params = await request.form() if request.method == "POST" else request.query_params
    sorted_items = sorted(params.items())
    data = url + ''.join(f"{k}{v}" for k, v in sorted_items)
    computed = base64.b64encode(hmac.new(auth_token.encode(), data.encode(), hashlib.sha1).digest()).decode()
    return hmac.compare_digest(signature, computed)

# --- Secrets Management ---
def get_secret(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Missing required secret: {name}")
    return value 