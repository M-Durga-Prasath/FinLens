
import os
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request

logger = logging.getLogger(__name__)


def _get_rate_limit_key(request: Request) -> str:
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt, os

            token = auth_header.split(" ", 1)[1]
            secret = os.getenv("BACKEND_AUTH_SECRET", "")
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            user_id = payload.get("userId")
            if user_id:
                return f"user:{user_id}"
        except Exception as exc:
            logger.warning("Rate-limit key extraction failed: %s", exc)

    return get_remote_address(request)


limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=["120/minute"],
    storage_uri=os.getenv("REDIS_URL", "memory://"),
)


def install_rate_limiter(app):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
