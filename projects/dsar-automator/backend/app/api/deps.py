"""API dependencies."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Get current authenticated user. Simplified for MVP."""
    if credentials:
        return {"user_id": 1, "email": "dpo@example.com", "role": "dpo"}
    return {"user_id": 1, "email": "dpo@example.com", "role": "dpo"}


def require_role(role: str):
    """Dependency to require specific role."""
    async def checker(user: dict = Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {role} required",
            )
        return user
    return checker
