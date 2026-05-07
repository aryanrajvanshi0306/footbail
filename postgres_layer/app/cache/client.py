"""Async Redis CacheClient — Layer 1B.

Singleton wrapper around `redis.asyncio` for the entire app.
Pool size 10. decode_responses=True. JSON helpers, hash/zset/pubsub support,
SETNX-style slot locks, pipeline context, and graceful degradation if Redis is down.
"""
from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from redis.asyncio import Redis, ConnectionPool
from redis.asyncio.client import Pipeline, PubSub

log = logging.getLogger("footbail.cache")

# Module-level singleton state
_pool: Optional[ConnectionPool] = None
_client: Optional["CacheClient"] = None


class CacheClient:
    """Async Redis facade. Construct via `await CacheClient.create()` or use `get_cache()`."""

    def __init__(self, redis: Redis) -> None:
        self._r = redis

    # ── Lifecycle ────────────────────────────────────────────────
    @classmethod
    async def create(cls, url: str, max_connections: int = 10) -> "CacheClient":
        global _pool
        _pool = ConnectionPool.from_url(
            url,
            max_connections=max_connections,
            decode_responses=True,
            health_check_interval=30,
            socket_connect_timeout=5,
            socket_keepalive=True,
        )
        client = Redis(connection_pool=_pool)
        await client.ping()
        log.info("CacheClient connected · pool=%d", max_connections)
        return cls(client)

    async def close(self) -> None:
        try:
            await self._r.aclose()
        except Exception:
            pass
        global _pool
        if _pool is not None:
            await _pool.aclose()
            _pool = None
        log.info("CacheClient closed")

    @property
    def raw(self) -> Redis:
        """Escape hatch for advanced commands — prefer typed methods."""
        return self._r

    async def ping(self) -> bool:
        try:
            return bool(await self._r.ping())
        except Exception as e:
            log.warning("Redis PING failed: %s", e)
            return False

    # ── String / JSON ────────────────────────────────────────────
    async def get_str(self, key: str) -> Optional[str]:
        return await self._r.get(key)

    async def set_str(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        await self._r.set(key, value, ex=ttl)

    async def get_json(self, key: str) -> Optional[Any]:
        raw = await self._r.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            log.warning("get_json: corrupt payload at %s", key)
            return None

    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        await self._r.set(key, json.dumps(value, separators=(",", ":"), default=str), ex=ttl)

    async def get_many_json(self, keys: list[str]) -> list[Optional[Any]]:
        if not keys:
            return []
        raws = await self._r.mget(keys)
        out: list[Optional[Any]] = []
        for r in raws:
            if r is None:
                out.append(None)
            else:
                try:
                    out.append(json.loads(r))
                except (ValueError, TypeError):
                    out.append(None)
        return out

    # ── Existence / Delete ───────────────────────────────────────
    async def exists(self, key: str) -> bool:
        return bool(await self._r.exists(key))

    async def delete(self, key: str) -> int:
        return int(await self._r.delete(key))

    async def delete_many(self, keys: list[str]) -> int:
        if not keys:
            return 0
        return int(await self._r.delete(*keys))

    async def expire(self, key: str, ttl: int) -> bool:
        return bool(await self._r.expire(key, ttl))

    # ── Counters ─────────────────────────────────────────────────
    async def increment(self, key: str, by: int = 1, ttl: Optional[int] = None) -> int:
        async with self._r.pipeline(transaction=False) as pipe:
            pipe.incrby(key, by)
            if ttl is not None:
                pipe.expire(key, ttl)
            results = await pipe.execute()
        return int(results[0])

    async def decrement(self, key: str, by: int = 1) -> int:
        return int(await self._r.decrby(key, by))

    # ── SETNX (atomic — slot locks, distributed locks) ───────────
    async def setnx(self, key: str, value: str, ttl: int) -> bool:
        """Atomic SET if not exists, with TTL. Returns True if acquired."""
        return bool(await self._r.set(key, value, ex=ttl, nx=True))

    async def release_lock(self, key: str, expected_value: str) -> bool:
        """Lua-atomic lock release — only delete if value matches."""
        script = """
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            return redis.call('DEL', KEYS[1])
        else
            return 0
        end
        """
        result = await self._r.eval(script, 1, key, expected_value)
        return int(result) == 1

    # ── Hash ─────────────────────────────────────────────────────
    async def hget(self, key: str, field: str) -> Optional[str]:
        return await self._r.hget(key, field)

    async def hset(self, key: str, field: str, value: str | int, ttl: Optional[int] = None) -> int:
        async with self._r.pipeline(transaction=False) as pipe:
            pipe.hset(key, field, value)
            if ttl is not None:
                pipe.expire(key, ttl)
            results = await pipe.execute()
        return int(results[0])

    async def hset_many(self, key: str, mapping: dict, ttl: Optional[int] = None) -> int:
        if not mapping:
            return 0
        async with self._r.pipeline(transaction=False) as pipe:
            pipe.hset(key, mapping=mapping)
            if ttl is not None:
                pipe.expire(key, ttl)
            results = await pipe.execute()
        return int(results[0])

    async def hgetall(self, key: str) -> dict[str, str]:
        return dict(await self._r.hgetall(key) or {})

    async def hdel(self, key: str, *fields: str) -> int:
        if not fields:
            return 0
        return int(await self._r.hdel(key, *fields))

    async def hincrby(self, key: str, field: str, by: int = 1) -> int:
        return int(await self._r.hincrby(key, field, by))

    # ── Sorted Set (leaderboards, LFG) ───────────────────────────
    async def zadd(self, key: str, mapping: dict[str, float], ttl: Optional[int] = None) -> int:
        if not mapping:
            return 0
        async with self._r.pipeline(transaction=False) as pipe:
            pipe.zadd(key, mapping)
            if ttl is not None:
                pipe.expire(key, ttl)
            results = await pipe.execute()
        return int(results[0])

    async def zincrby(self, key: str, member: str, by: float = 1.0) -> float:
        """Increment leaderboard score for a single member."""
        return float(await self._r.zincrby(key, by, member))

    async def zscore(self, key: str, member: str) -> Optional[float]:
        score = await self._r.zscore(key, member)
        return float(score) if score is not None else None

    async def zrank(self, key: str, member: str, descending: bool = True) -> Optional[int]:
        """Returns 0-based rank. descending=True → highest score = rank 0."""
        if descending:
            r = await self._r.zrevrank(key, member)
        else:
            r = await self._r.zrank(key, member)
        return int(r) if r is not None else None

    async def zrevrange_withscores(
        self, key: str, start: int = 0, end: int = -1
    ) -> list[tuple[str, float]]:
        """Top-N leaderboard slice with scores (descending)."""
        raw = await self._r.zrevrange(key, start, end, withscores=True)
        return [(m, float(s)) for m, s in raw]

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        """Auto-cleanup expired LFG entries (score=expires_at_unix < now)."""
        return int(await self._r.zremrangebyscore(key, min_score, max_score))

    async def zrem(self, key: str, *members: str) -> int:
        if not members:
            return 0
        return int(await self._r.zrem(key, *members))

    async def zcard(self, key: str) -> int:
        return int(await self._r.zcard(key))

    # ── Set (membership, viewer counts) ──────────────────────────
    async def sadd(self, key: str, *members: str, ttl: Optional[int] = None) -> int:
        if not members:
            return 0
        async with self._r.pipeline(transaction=False) as pipe:
            pipe.sadd(key, *members)
            if ttl is not None:
                pipe.expire(key, ttl)
            results = await pipe.execute()
        return int(results[0])

    async def srem(self, key: str, *members: str) -> int:
        if not members:
            return 0
        return int(await self._r.srem(key, *members))

    async def scard(self, key: str) -> int:
        return int(await self._r.scard(key))

    async def smembers(self, key: str) -> set[str]:
        raw = await self._r.smembers(key) or set()
        return {m for m in raw}

    # ── List (event streams, queues) ─────────────────────────────
    async def lpush(self, key: str, *values: str, ttl: Optional[int] = None, max_len: Optional[int] = None) -> int:
        if not values:
            return 0
        async with self._r.pipeline(transaction=False) as pipe:
            pipe.lpush(key, *values)
            if max_len is not None:
                pipe.ltrim(key, 0, max_len - 1)
            if ttl is not None:
                pipe.expire(key, ttl)
            results = await pipe.execute()
        return int(results[0])

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list[str]:
        return list(await self._r.lrange(key, start, end) or [])

    async def llen(self, key: str) -> int:
        return int(await self._r.llen(key))

    # ── Pub/Sub ──────────────────────────────────────────────────
    async def publish(self, channel: str, message: Any) -> int:
        payload = message if isinstance(message, str) else json.dumps(message, default=str)
        return int(await self._r.publish(channel, payload))

    def subscribe(self) -> PubSub:
        """Returns a PubSub object — caller is responsible for `await ps.subscribe(channel)`
        and `async for msg in ps.listen(): ...`. Always `await ps.aclose()` on shutdown."""
        return self._r.pubsub()

    # ── Pipeline ─────────────────────────────────────────────────
    @asynccontextmanager
    async def pipeline(self, transaction: bool = False) -> AsyncIterator[Pipeline]:
        """Async pipeline context. Use for batched ops.

        Example:
            async with cache.pipeline() as pipe:
                pipe.set("a", "1")
                pipe.set("b", "2")
                results = await pipe.execute()
        """
        async with self._r.pipeline(transaction=transaction) as pipe:
            yield pipe


# ─────────────────────────── Module-level singleton ───────────────────────────
async def init_cache(url: Optional[str] = None) -> CacheClient:
    """Idempotent — call once during FastAPI startup."""
    global _client
    if _client is not None:
        return _client
    redis_url = url or os.environ.get("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL env var not set — required for CacheClient")
    _client = await CacheClient.create(redis_url, max_connections=10)
    return _client


def get_cache() -> CacheClient:
    """Used as FastAPI dependency or anywhere in the app after startup."""
    if _client is None:
        raise RuntimeError("CacheClient not initialised — did you forget the FastAPI lifespan?")
    return _client


async def close_cache() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
