import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from .schemas import CurrentUser

ALGORITHM = os.getenv("ALGORITHM")
SECRET_KEY = os.getenv("SECRET_KEY")

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "access":
        
            raise credentials_exception

        user_id = payload.get("sub") or payload.get("user_id")
        company_id = payload.get("company_id")

        if user_id is None or company_id is None:
            raise credentials_exception

        return CurrentUser(user_id=int(user_id), company_id=int(company_id))

    except (jwt.PyJWTError, ValueError) as exc:
        raise credentials_exception
    except HTTPException:
        raise
    except Exception as exc:
        raise credentials_exception
