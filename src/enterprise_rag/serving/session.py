"""Signed demo sessions: the role travels in a server-signed cookie, never in the request.

The demo has no company login, so picking a role stands in for signing in. The server signs
the role with HMAC; a cookie edited in the browser fails verification and is rejected.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from collections.abc import Sequence

COOKIE = "session"
MAX_AGE_S = 7 * 24 * 3600


class SessionSigner:
    def __init__(self, roles: Sequence[str], secret: str | None = None, max_age_s: int = MAX_AGE_S):
        self.roles = set(roles)
        self.max_age_s = max_age_s
        self._key = (secret or secrets.token_hex(32)).encode()

    def _sign(self, body: str) -> str:
        mac = hmac.new(self._key, body.encode(), hashlib.sha256).digest()
        return base64.urlsafe_b64encode(mac).decode().rstrip("=")

    def issue(self, role: str, now: float | None = None) -> str:
        if role not in self.roles:
            raise ValueError(f"unknown role {role!r}")
        body = f"{role}.{int(now if now is not None else time.time())}"
        return f"{body}.{self._sign(body)}"

    def verify(self, token: str | None, now: float | None = None) -> str | None:
        """The role in a valid, unexpired token; None for anything else."""
        if not token or token.count(".") != 2:
            return None
        role, issued, sig = token.split(".")
        if not hmac.compare_digest(sig, self._sign(f"{role}.{issued}")):
            return None
        if not issued.isdigit() or (now or time.time()) - int(issued) > self.max_age_s:
            return None
        return role if role in self.roles else None
