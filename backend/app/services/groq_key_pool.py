"""Round-robin pool of Groq API keys with cooldown-aware failover.

Why: providers rate-limit per API key. With N keys, effective capacity is
N x the single-key limit. When one key returns 429, we put it in cooldown
for the duration the provider suggests and immediately retry on the next
healthy key, instead of sleeping while other keys still have budget.
"""
import threading
import time


class AllKeysCoolingDown(Exception):
    """Raised when every key in the pool is in cooldown."""


class GroqKeyPool:
    def __init__(self, api_keys: list[str]):
        # Preserve order, drop empties/duplicates
        seen: set[str] = set()
        self._keys = [k for k in api_keys if k and not (k in seen or seen.add(k))]
        self._cooldowns: dict[str, float] = {}  # key -> epoch seconds when it frees up
        self._lock = threading.Lock()
        self._cursor = 0

    def __len__(self) -> int:
        return len(self._keys)

    def _healthy_keys(self, now: float) -> list[str]:
        return [k for k in self._keys if self._cooldowns.get(k, 0) <= now]

    def acquire(self) -> str:
        """Return the next healthy key (round-robin). Raises AllKeysCoolingDown
        if every key is rate-limited; the exception carries the earliest wake time."""
        now = time.monotonic()
        with self._lock:
            healthy = self._healthy_keys(now)
            if not healthy:
                earliest = min(self._cooldowns.get(k, 0) for k in self._keys)
                raise AllKeysCoolingDown(
                    f"all {len(self._keys)} Groq keys cooling down, earliest frees in {earliest - now:.0f}s"
                )
            # Round-robin over healthy keys only
            key = healthy[self._cursor % len(healthy)]
            self._cursor = (self._cursor + 1) % max(len(healthy), 1)
            return key

    def report_rate_limited(self, key: str, cooldown_seconds: float) -> None:
        """Mark a key as cooling down until cooldown_seconds from now."""
        with self._lock:
            self._cooldowns[key] = time.monotonic() + max(cooldown_seconds, 1.0)

    def report_success(self, key: str) -> None:
        """A successful call clears any stale cooldown on the key."""
        with self._lock:
            self._cooldowns.pop(key, None)

    def status(self) -> dict:
        """Observability snapshot: total/healthy keys and remaining cooldowns."""
        now = time.monotonic()
        with self._lock:
            cooling = {
                k[-6:]: round(self._cooldowns[k] - now, 1)
                for k in self._keys
                if self._cooldowns.get(k, 0) > now
            }
            return {"total_keys": len(self._keys), "healthy": len(self._keys) - len(cooling), "cooling": cooling}
