import os

import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")

class TokenUser:
    def __init__(self,payload: dict):
        self.id = int(payload.get('user_id') or payload.get("sub"))
        self.company_id = int(payload.get('company_id'))
        self.role = payload.get('role')
        self.is_authenticated = True

    def __str__(self):
        return f"User {self.id} (Company {self.company_id})"

class StatelessJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        token = parts[1]
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )
            user_id = payload.get("user_id") or payload.get("sub")
            company_id = payload.get("company_id")
            if not user_id or not company_id:
                raise AuthenticationFailed("Невалидный токен: отсутствуют user_id или company_id")
            return (TokenUser(payload), None)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Срок действия токена истек")
        except jwt.PyJWTError:
            raise AuthenticationFailed("Ошибка проверки подписи токена")