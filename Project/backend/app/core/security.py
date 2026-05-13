"""
DRIP — Seguridad y autenticación
Implementación simple para prototipo — JWT mock
"""

from datetime import datetime, timedelta
from typing import Optional
import hashlib
import hmac

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash simple de contraseña con HMAC-SHA256."""
    return hmac.new(
        settings.SECRET_KEY.encode(),
        password.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica contraseña contra el hash almacenado."""
    return hmac.compare_digest(hash_password(plain), hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Genera un token de acceso simple codificado en base64.
    Para producción usar python-jose con JWT real.
    """
    import base64
    import json

    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {**data, "exp": expire.isoformat(), "iss": "DRIP-AgTech"}
    raw = json.dumps(payload).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica el token y valida expiración."""
    import base64
    import json

    try:
        raw = base64.urlsafe_b64decode(token.encode())
        payload = json.loads(raw)
        exp = datetime.fromisoformat(payload["exp"])
        if datetime.utcnow() > exp:
            return None
        return payload
    except Exception:
        return None


# Usuario demo hardcodeado para prototipo
DEMO_USERS = {
    settings.DEMO_USER.lower(): {
        "username": settings.DEMO_USER,
        "full_name": "Danae Ramírez",
        "email": "danae@drip.agtech",
        "role": "admin",
        "hashed_password": hash_password(settings.DEMO_PASSWORD),
    }
}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Autentica usuario contra los usuarios demo."""
    user = DEMO_USERS.get(username.lower())
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user
