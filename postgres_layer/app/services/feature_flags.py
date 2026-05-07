"""Feature Flag Service — Layer 1B.

Twelve flags drive Free / Pro / Academy gating across the 16 modules.
Flag config is seeded into Redis on startup (idempotent), then read on every
gate-check (cached at the HASH level — single round-trip).

Admin override: `PATCH /v2/admin/feature-flags/{key}` (handled by the route layer
in Layer 2; this module exposes the underlying mutation function).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Final, Literal, Optional, TypedDict

from app.cache.client import CacheClient, get_cache
from app.cache.keys import MISC, PUBSUB

log = logging.getLogger("footbail.flags")

Tier = Literal["free", "pro", "academy"]
TIERS: Final[tuple[Tier, ...]] = ("free", "pro", "academy")


class FlagConfig(TypedDict, total=False):
    """Per-flag config persisted in Redis as the value of HASH ff:flags[<code>]."""
    code: str
    label: str
    description: str
    tiers: dict[str, Any]               # {"free": False|True|<value>, "pro": ..., "academy": ...}
    chat_limit_per_day: dict[str, Any]  # ai_coach_chat only
    referee_only: bool
    overridden: bool                    # admin override marker
    updated_at: Optional[str]


# ─────────────────────────── DEFAULT_FLAGS ───────────────────────────
# 12 flags · tier defaults aligned with PRD's data-flywheel intent.
DEFAULT_FLAGS: Final[dict[str, FlagConfig]] = {
    "pre_match_intelligence": {
        "code": "pre_match_intelligence",
        "label": "Pre-Match Intelligence Pack",
        "description": "Win probability, AI tactical brief, key matchup, role card.",
        "tiers": {"free": "basic", "pro": "full", "academy": "full"},
        "referee_only": False,
        "overridden": False,
    },
    "match_impact_index": {
        "code": "match_impact_index",
        "label": "Match Impact Index",
        "description": "0–100 impact score per player + Impact Hero spotlight.",
        # Visible to all — drives engagement; deeper breakdown gated to Pro+.
        "tiers": {"free": "score_only", "pro": "with_breakdown", "academy": "with_breakdown_history"},
        "referee_only": False,
        "overridden": False,
    },
    "ai_tactics": {
        "code": "ai_tactics",
        "label": "AI Tactical Assistant",
        "description": "Pre-match plan, live in-match tips, post-match autopsy.",
        "tiers": {"free": False, "pro": True, "academy": True},
        "referee_only": False,
        "overridden": False,
    },
    "story_mode": {
        "code": "story_mode",
        "label": "Match Story Mode",
        "description": "Instagram-style match recap with Clutch Detector.",
        # Free gets a 3-event stub; Pro/Academy get full reel.
        "tiers": {"free": "stub_3", "pro": "full", "academy": "full"},
        "referee_only": False,
        "overridden": False,
    },
    "ai_coach_chat": {
        "code": "ai_coach_chat",
        "label": "Personal AI Coach Chat",
        "description": "Persistent chat with rate-limited GPT-4o coach.",
        "tiers": {"free": True, "pro": True, "academy": True},
        # Per-day prompt limits — read by get_chat_limit().
        "chat_limit_per_day": {"free": 5, "pro": 20, "academy": -1},  # -1 = unlimited
        "referee_only": False,
        "overridden": False,
    },
    "play_style_dna": {
        "code": "play_style_dna",
        "label": "Play Style DNA",
        "description": "AI-generated archetype label and trait scores.",
        "tiers": {"free": False, "pro": True, "academy": True},
        "referee_only": False,
        "overridden": False,
    },
    "live_match_ux": {
        "code": "live_match_ux",
        "label": "Live Match UX",
        "description": "Real-time score, events feed, broadcast viewer.",
        # Always on — this is the hero loop.
        "tiers": {"free": True, "pro": True, "academy": True},
        "referee_only": False,
        "overridden": False,
    },
    "smart_matchmaking": {
        "code": "smart_matchmaking",
        "label": "Smart Matchmaking & LFG",
        "description": "Looking-For-Game broadcasts + proximity matching.",
        "tiers": {"free": True, "pro": True, "academy": True},
        "referee_only": False,
        "overridden": False,
    },
    "career_growth_tracker": {
        "code": "career_growth_tracker",
        "label": "Career Growth Tracker",
        "description": "Form graph, peer percentile, role-based stats.",
        "tiers": {"free": "basic", "pro": "full", "academy": "full"},
        "referee_only": False,
        "overridden": False,
    },
    "ai_drill_recommender": {
        "code": "ai_drill_recommender",
        "label": "AI Drill Recommender",
        "description": "Personal drill assignments based on weakness vector.",
        "tiers": {"free": False, "pro": True, "academy": True},
        "referee_only": False,
        "overridden": False,
    },
    "share_everywhere": {
        "code": "share_everywhere",
        "label": "Share Everywhere",
        "description": "One-tap WhatsApp / Instagram share for cards, goals, stories.",
        "tiers": {"free": True, "pro": True, "academy": True},  # always on — viral loop
        "referee_only": False,
        "overridden": False,
    },
    "referee_training": {
        "code": "referee_training",
        "label": "Referee Training",
        "description": "Module catalog, quizzes, tier progression for referees.",
        "tiers": {"free": True, "pro": True, "academy": True},
        "referee_only": True,  # gated by role at the route layer
        "overridden": False,
    },
}

assert len(DEFAULT_FLAGS) == 12, "Layer 1B requires exactly 12 feature flags"


# ─────────────────────────── Seeding ───────────────────────────
async def seed_feature_flags(cache: Optional[CacheClient] = None, *, force: bool = False) -> int:
    """Idempotent — adds any missing flags to ff:flags HASH. Existing overrides preserved."""
    cache = cache or get_cache()
    existing = await cache.hgetall(MISC.FEATURE_FLAGS)
    seeded = 0
    mapping: dict[str, str] = {}
    for code, cfg in DEFAULT_FLAGS.items():
        if force or code not in existing:
            mapping[code] = json.dumps(cfg, separators=(",", ":"))
            seeded += 1
    if mapping:
        await cache.hset_many(MISC.FEATURE_FLAGS, mapping)
        await cache.increment(MISC.FEATURE_FLAGS_VERSION, by=1)
        await cache.publish(PUBSUB.FEATURE_FLAG_UPDATED, {"seeded": list(mapping.keys())})
    log.info("Feature flags seeded · added=%d total=%d", seeded, len(DEFAULT_FLAGS))
    return seeded


# ─────────────────────────── Read API ───────────────────────────
async def get_flag(code: str, *, cache: Optional[CacheClient] = None) -> Optional[FlagConfig]:
    """Returns the flag's config dict or None if unknown."""
    cache = cache or get_cache()
    raw = await cache.hget(MISC.FEATURE_FLAGS, code)
    if raw is None:
        # Fall back to in-memory default if Redis seed hasn't run for some reason.
        return DEFAULT_FLAGS.get(code)
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return DEFAULT_FLAGS.get(code)


async def get_all_flags(*, cache: Optional[CacheClient] = None) -> dict[str, FlagConfig]:
    cache = cache or get_cache()
    raw = await cache.hgetall(MISC.FEATURE_FLAGS)
    out: dict[str, FlagConfig] = {}
    for code, payload in raw.items():
        try:
            out[code] = json.loads(payload)
        except (ValueError, TypeError):
            if code in DEFAULT_FLAGS:
                out[code] = DEFAULT_FLAGS[code]
    # Add anything missing from in-memory defaults (defensive)
    for code, cfg in DEFAULT_FLAGS.items():
        out.setdefault(code, cfg)
    return out


async def is_enabled(code: str, tier: Tier, *, cache: Optional[CacheClient] = None) -> bool:
    """Truthy gate-check.

    For tier values like 'basic' / 'stub_3' / 'full' / 'score_only' (all string truthy),
    this returns True — caller should use `get_flag` if the *level* matters.
    """
    if tier not in TIERS:
        return False
    cfg = await get_flag(code, cache=cache)
    if not cfg:
        return False
    val = cfg.get("tiers", {}).get(tier)
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    # Strings like "basic"/"full"/"stub_3" are all on
    if isinstance(val, str):
        return val not in {"", "off", "disabled", "false"}
    return bool(val)


async def get_flag_level(code: str, tier: Tier, *, cache: Optional[CacheClient] = None) -> Optional[Any]:
    """Returns the raw tier value — useful when level matters (basic vs full vs stub_3)."""
    cfg = await get_flag(code, cache=cache)
    if not cfg:
        return None
    return cfg.get("tiers", {}).get(tier)


async def get_chat_limit(tier: Tier, *, cache: Optional[CacheClient] = None) -> int:
    """Returns daily AI Coach Chat prompt limit. -1 = unlimited."""
    cfg = await get_flag("ai_coach_chat", cache=cache)
    if not cfg:
        return 0
    limits = cfg.get("chat_limit_per_day", {}) or {}
    val = limits.get(tier, 0)
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


# ─────────────────────────── Write API (admin override) ───────────────────────────
async def update_flag(
    code: str,
    *,
    tiers: Optional[dict[str, Any]] = None,
    chat_limit_per_day: Optional[dict[str, Any]] = None,
    label: Optional[str] = None,
    description: Optional[str] = None,
    cache: Optional[CacheClient] = None,
) -> FlagConfig:
    """Admin override — surgical update of a flag's config. Bumps version + pubsubs.

    Wired from `PATCH /v2/admin/feature-flags/{key}` in Layer 2.
    """
    cache = cache or get_cache()
    if code not in DEFAULT_FLAGS:
        raise ValueError(f"Unknown feature flag: {code}")
    current = await get_flag(code, cache=cache) or dict(DEFAULT_FLAGS[code])
    cfg: FlagConfig = dict(current)  # shallow copy
    if tiers is not None:
        merged = dict(cfg.get("tiers", {}))
        merged.update(tiers)
        cfg["tiers"] = merged
    if chat_limit_per_day is not None:
        merged_limits = dict(cfg.get("chat_limit_per_day", {}) or {})
        merged_limits.update(chat_limit_per_day)
        cfg["chat_limit_per_day"] = merged_limits
    if label is not None:
        cfg["label"] = label
    if description is not None:
        cfg["description"] = description
    cfg["overridden"] = True
    from datetime import datetime, timezone
    cfg["updated_at"] = datetime.now(timezone.utc).isoformat()

    await cache.hset(MISC.FEATURE_FLAGS, code, json.dumps(cfg, separators=(",", ":")))
    await cache.increment(MISC.FEATURE_FLAGS_VERSION, by=1)
    await cache.publish(PUBSUB.FEATURE_FLAG_UPDATED, {"code": code})
    log.info("Feature flag updated · %s", code)
    return cfg


async def reset_flag(code: str, *, cache: Optional[CacheClient] = None) -> FlagConfig:
    """Revert a single flag to DEFAULT_FLAGS."""
    cache = cache or get_cache()
    if code not in DEFAULT_FLAGS:
        raise ValueError(f"Unknown feature flag: {code}")
    cfg = dict(DEFAULT_FLAGS[code])
    cfg["overridden"] = False
    await cache.hset(MISC.FEATURE_FLAGS, code, json.dumps(cfg, separators=(",", ":")))
    await cache.increment(MISC.FEATURE_FLAGS_VERSION, by=1)
    await cache.publish(PUBSUB.FEATURE_FLAG_UPDATED, {"code": code, "reset": True})
    log.info("Feature flag reset · %s", code)
    return cfg


__all__ = [
    "Tier", "TIERS", "FlagConfig", "DEFAULT_FLAGS",
    "seed_feature_flags",
    "get_flag", "get_all_flags", "get_flag_level",
    "is_enabled", "get_chat_limit",
    "update_flag", "reset_flag",
]
