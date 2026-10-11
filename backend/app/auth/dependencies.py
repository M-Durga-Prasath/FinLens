import os
import logging
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.database import get_db

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(
    description="JWT token issue by frontend at route /api/auth/backend-token endpoint"
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    Auth_Key = os.getenv("BACKEND_AUTH_SECRET")

    if not Auth_Key:
        logger.error("BACKEND_AUTH_SECRET is not set.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail = "Authoriazation key is not present."
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            Auth_Key,
            algorithms=["HS256"]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Token has expired. Please try again."
    )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid authentication token"
        )
    
    user_id = payload.get("userId")
    if not user_id:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Token Missing user details"
        )
    
    return {
        "userId": user_id,
        "email": payload.get("email"),
    }


async def verify_session_access(session_id, user_id: str) -> None:

    try:
        pool = await get_db()
        async with pool.acquire() as conn:
            session_owner = await conn.fetchval(
                'SELECT "userId" FROM sessions WHERE id = $1',
                str(session_id),
            )
            if session_owner and str(session_owner) != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this session.",
                )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Could not verify session ownership: %s", exc)