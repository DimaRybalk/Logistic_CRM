import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import RoleEnum, UserModel
from app.security import ALGORITHM, SECRET_KEY

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):

    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_type = payload.get("type")

    if token_type != "access":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type, access token required",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User identifier missing in token",
        )

    query = select(UserModel).where(UserModel.id == int(user_id))
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive user",
        )

    return user, payload.get("company_id"), payload.get("role")


def require_role(allowed_role: RoleEnum):
    async def role_checker(
        auth_data: tuple[UserModel, int, str] = Depends(get_current_user),
    ):
        user, company_id, role = auth_data

        if role != allowed_role.value:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions for this action",
            )

        return auth_data

    return role_checker
