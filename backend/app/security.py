"""Авторизация всех ресурсов панели; секреты остаются на сервере."""
import base64
import binascii
import hmac
import os
import re
from urllib.parse import urlsplit

from starlette.responses import JSONResponse


def redact(value):
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if not isinstance(value, str):
        return value
    for name in ("OPENROUTER_API_KEY", "PANEL_PASSWORD"):
        secret = os.environ.get(name, "")
        if secret:
            value = value.replace(secret, "[REDACTED]")
    value = re.sub(r"(?i)(Bearer\s+)[\w.\-/+=]+", r"\1[REDACTED]", value)
    value = re.sub(r"\bsk-[\w-]+", "[REDACTED]", value)
    return value


async def secure_request(request, call_next):
    host = request.headers.get("host", "")
    try:
        hostname = urlsplit("//" + host).hostname
    except ValueError:
        hostname = None
    if hostname not in {"localhost", "127.0.0.1", "::1"}:
        return JSONResponse({"detail": "Доступ только через локальный SSH tunnel"}, status_code=400)
    password = os.environ.get("PANEL_PASSWORD", "")
    username = os.environ.get("PANEL_USER", "owner")
    if len(password) < 32:
        return JSONResponse({"detail": "На сервере требуется PANEL_PASSWORD длиной минимум 32 символа"}, status_code=503)
    try:
        scheme, token = request.headers.get("authorization", "").split(" ", 1)
        user, supplied = base64.b64decode(token, validate=True).decode().split(":", 1)
        valid = scheme.lower() == "basic" and hmac.compare_digest(user.encode(), username.encode()) and hmac.compare_digest(supplied.encode(), password.encode())
    except (ValueError, UnicodeError, binascii.Error):
        valid = False
    if not valid:
        return JSONResponse({"detail": "Требуется авторизация владельца"}, status_code=401,
                            headers={"WWW-Authenticate": 'Basic realm="AICommander", charset="UTF-8"'})
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if request.headers.get("x-aicommander-request") != "1" or (origin and origin != str(request.base_url).rstrip("/")):
            return JSONResponse({"detail": "Запрос отклонён защитой CSRF"}, status_code=403)
    response = await call_next(request)
    response.headers.update({
        "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
    })
    return response


class RedactedJSONResponse(JSONResponse):
    def render(self, content):
        return super().render(redact(content))
