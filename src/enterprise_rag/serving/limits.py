"""Per-visitor rate limits and an answer cache, so a public demo stays inside Groq's quota."""

from __future__ import annotations

import time
from collections import OrderedDict, defaultdict, deque

MINUTE_S, DAY_S = 60, 24 * 3600


class RateLimiter:
    def __init__(self, per_minute: int, per_day: int):
        self.per_minute, self.per_day = per_minute, per_day
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, now: float | None = None) -> int:
        """0 if the call is allowed (and records it), else seconds to wait."""
        now = time.time() if now is None else now
        hits = self._hits[key]
        while hits and now - hits[0] > DAY_S:
            hits.popleft()
        last_minute = [t for t in hits if now - t < MINUTE_S]
        if len(last_minute) >= self.per_minute:
            return int(MINUTE_S - (now - last_minute[0])) + 1
        if len(hits) >= self.per_day:
            return int(DAY_S - (now - hits[0])) + 1
        hits.append(now)
        return 0


class AnswerCache:
    """Small LRU keyed by (role, normalized question)."""

    def __init__(self, size: int = 512):
        self.size = size
        self._data: OrderedDict[tuple[str, str], dict] = OrderedDict()

    @staticmethod
    def key(role: str, question: str) -> tuple[str, str]:
        return role, " ".join(question.lower().split())

    def get(self, role: str, question: str) -> dict | None:
        k = self.key(role, question)
        if k in self._data:
            self._data.move_to_end(k)
            return self._data[k]
        return None

    def put(self, role: str, question: str, value: dict) -> None:
        self._data[self.key(role, question)] = value
        self._data.move_to_end(self.key(role, question))
        while len(self._data) > self.size:
            self._data.popitem(last=False)
