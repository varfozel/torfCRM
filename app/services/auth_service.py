import base64
import hashlib
import hmac
import json
import time
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


class ManagerUser(BaseModel):
    username: str
    role: str = "manager"
    name: str = "Менеджер Peat CRM"


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


class AuthService:
    """Authentication and JWT service for Peat CRM Manager."""

    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY.encode("utf-8")
        self.algorithm = "HS256"

    def verify_password(self, plain_password: str, expected_password: str) -> bool:
        """Constant-time password comparison to prevent timing attacks."""
        return hmac.compare_digest(plain_password.encode("utf-8"), expected_password.encode("utf-8"))

    def authenticate_manager(self, username: str, password: str) -> Optional[ManagerUser]:
        if (
            username == settings.MANAGER_USERNAME
            and self.verify_password(password, settings.MANAGER_PASSWORD)
        ):
            return ManagerUser(username=username, role="manager", name="Головний менеджер")
        return None

    def create_access_token(self, username: str, expires_minutes: Optional[int] = None) -> str:
        if expires_minutes is None:
            expires_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

        now = int(time.time())
        exp = now + (expires_minutes * 60)

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": username,
            "role": "manager",
            "iat": now,
            "exp": exp,
        }

        header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        signature = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        signature_b64 = _b64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def decode_access_token(self, token: str) -> Optional[dict]:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            header_b64, payload_b64, signature_b64 = parts

            signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
            expected_sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
            actual_sig = _b64url_decode(signature_b64)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return None

            payload_bytes = _b64url_decode(payload_b64)
            payload = json.loads(payload_bytes.decode("utf-8"))

            now = int(time.time())
            if payload.get("exp", 0) < now:
                return None

            return payload
        except Exception:
            return None


auth_service = AuthService()


async def get_current_manager(
    authorization: Optional[str] = Header(None),
) -> ManagerUser:
    """Dependency to validate manager token from Authorization: Bearer <token> header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Потрібна авторизація менеджера",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірний формат токена авторизації (очікується 'Bearer <token>')",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    payload = auth_service.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен авторизації недійсний або його термін дії закінчився",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return ManagerUser(
        username=payload.get("sub", settings.MANAGER_USERNAME),
        role=payload.get("role", "manager"),
        name="Головний менеджер",
    )


async def get_optional_manager(
    authorization: Optional[str] = Header(None),
) -> Optional[ManagerUser]:
    """Dependency that returns ManagerUser if valid token provided, else None."""
    if not authorization:
        return None
    try:
        return await get_current_manager(authorization=authorization)
    except HTTPException:
        return None
