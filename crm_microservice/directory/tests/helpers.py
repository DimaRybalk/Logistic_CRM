from datetime import datetime, timedelta, timezone
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM")


def create_token(company_id: int, role: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {
        "sub": "1",
        "company_id": company_id,
        "role": role,
        "type": "access",
        "exp": expire
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token