"""Redis key constants with TTLs — Layer 1B.

Format convention:
  - Colon-separated hierarchical keys.
  - Templates use {placeholder} for f-string formatting.
  - Every key has a TTL constant (seconds). Set TTL_FOREVER=None for non-expiring.
  - Sorted-set keys (zset) and list keys flagged in the docstring.
  - Pub/Sub channels live in the PUBSUB group; channels never expire.

Eviction policy assumed: allkeys-lru. Hot product caches use small TTLs;
auth tokens use exact lifetimes; leaderboards & feature flags persist.
"""
from __future__ import annotations

from typing import Final


TTL_FOREVER: Final[int | None] = None

# ─────────────────────────── AUTH ───────────────────────────
class AUTH:
    """Phone OTP, refresh token rotation, login rate-limits."""
    OTP_PHONE = "auth:otp:phone:{phone}"                        # SET, value=hashed otp
    OTP_PHONE_TTL: Final[int] = 5 * 60                          # 5 min
    OTP_ATTEMPTS = "auth:otp:attempts:{phone}"                  # INCR
    OTP_ATTEMPTS_TTL: Final[int] = 15 * 60
    REFRESH_BLOCKLIST = "auth:refresh:blocklist:{jti}"          # SET on logout/rotate
    REFRESH_BLOCKLIST_TTL: Final[int] = 30 * 24 * 60 * 60       # 30d (refresh token lifetime)
    LOGIN_RATELIMIT_PHONE = "auth:rl:login:phone:{phone}"
    LOGIN_RATELIMIT_PHONE_TTL: Final[int] = 60 * 60             # 1h
    LOGIN_RATELIMIT_IP = "auth:rl:login:ip:{ip}"
    LOGIN_RATELIMIT_IP_TTL: Final[int] = 60 * 60
    SESSION = "auth:session:{user_id}:{device_id}"
    SESSION_TTL: Final[int] = 30 * 24 * 60 * 60                 # 30d


# ─────────────────────────── USER ───────────────────────────
class USER:
    """Profile, player card, online presence."""
    PROFILE = "user:profile:{user_id}"                          # JSON
    PROFILE_TTL: Final[int] = 5 * 60                            # 5 min
    PLAYER_CARD = "user:card:{user_id}"                         # JSON full FIFA card
    PLAYER_CARD_TTL: Final[int] = 10 * 60
    OYP_PROFILE = "user:oyp:{user_id}"                          # JSON Play Style DNA
    OYP_PROFILE_TTL: Final[int] = 60 * 60
    PRESENCE = "user:presence:{user_id}"                        # SET "online"
    PRESENCE_TTL: Final[int] = 90                               # 90s heartbeat
    BY_PHONE = "user:by_phone:{phone}"                          # user_id lookup
    BY_PHONE_TTL: Final[int] = 60 * 60


# ─────────────────────────── MATCH ───────────────────────────
class MATCH:
    """Match detail, live state, event stream, slot locks (SETNX)."""
    DETAIL = "match:detail:{match_id}"                          # JSON
    DETAIL_TTL: Final[int] = 2 * 60
    EVENTS_LIST = "match:events:{match_id}"                     # LPUSH list of JSON event strings
    EVENTS_LIST_TTL: Final[int] = 6 * 60 * 60                   # 6h after match
    LIVE_STATE = "match:live:{match_id}"                        # JSON {clock, score, last_event_id}
    LIVE_STATE_TTL: Final[int] = 3 * 60 * 60
    SCORE = "match:score:{match_id}"                            # HASH {home, away}
    SCORE_TTL: Final[int] = 3 * 60 * 60
    BRIEF = "match:brief:{match_id}"                            # JSON pre-match brief (Module 03)
    BRIEF_TTL: Final[int] = 24 * 60 * 60
    ANALYSIS = "match:analysis:{match_id}"                      # JSON post-match analysis (Module 04)
    ANALYSIS_TTL: Final[int] = 7 * 24 * 60 * 60
    SLOT_LOCK = "match:slot_lock:{turf_id}:{slot_iso}"          # SETNX 5-min lock during checkout
    SLOT_LOCK_TTL: Final[int] = 5 * 60
    BROADCAST_VIEWERS = "match:viewers:{match_id}"              # SCARD


# ─────────────────────────── TURF ───────────────────────────
class TURF:
    DETAIL = "turf:detail:{turf_id}"                            # JSON
    DETAIL_TTL: Final[int] = 5 * 60
    AVAILABILITY = "turf:avail:{turf_id}:{date}"                # JSON [{slot, available}]
    AVAILABILITY_TTL: Final[int] = 60                           # short — slots churn
    CITY_LIST = "turf:list:{city}"                              # JSON list
    CITY_LIST_TTL: Final[int] = 5 * 60


# ─────────────────────────── VIDEO ───────────────────────────
class VIDEO:
    STATUS = "video:status:{video_id}"                          # SET status string
    STATUS_TTL: Final[int] = 6 * 60 * 60
    HLS_URL = "video:hls:{video_id}"                            # SET signed URL
    HLS_URL_TTL: Final[int] = 60 * 60
    PROCESSING_QUEUE_DEPTH = "video:queue:depth"                # GAUGE counter
    PROCESSING_QUEUE_DEPTH_TTL = TTL_FOREVER


# ─────────────────────────── SOCIAL ───────────────────────────
class SOCIAL:
    HOME_FEED = "feed:home:{user_id}"                           # JSON list of post ids
    HOME_FEED_TTL: Final[int] = 2 * 60
    CITY_FEED = "feed:city:{city}"                              # JSON
    CITY_FEED_TTL: Final[int] = 60
    POST = "post:detail:{post_id}"                              # JSON
    POST_TTL: Final[int] = 5 * 60
    REACTION_COUNTS = "post:reactions:{post_id}"                # HASH {boot,gloves,...}
    REACTION_COUNTS_TTL: Final[int] = 5 * 60
    USER_RECENT_POSTS = "user:posts:recent:{user_id}"           # LIST capped at 50
    USER_RECENT_POSTS_TTL: Final[int] = 60 * 60


# ─────────────────────────── GAMIFICATION (leaderboards: ZSETs) ───────────────────────────
class GAMIFICATION:
    LEADERBOARD_GLOBAL_XP = "lb:global:xp"                      # ZSET — score=xp
    LEADERBOARD_GLOBAL_XP_TTL = TTL_FOREVER
    LEADERBOARD_CITY_XP = "lb:city:{city}:xp"                   # ZSET
    LEADERBOARD_CITY_XP_TTL: Final[int] = 7 * 24 * 60 * 60
    LEADERBOARD_CITY_GOALS = "lb:city:{city}:goals"             # ZSET
    LEADERBOARD_CITY_GOALS_TTL: Final[int] = 7 * 24 * 60 * 60
    LEADERBOARD_CLUB = "lb:club:{club_id}:{metric}"             # ZSET
    LEADERBOARD_CLUB_TTL: Final[int] = 7 * 24 * 60 * 60
    DERBY_SCOREBOARD = "lb:derby:cities"                        # ZSET — score=aggregated city score
    DERBY_SCOREBOARD_TTL: Final[int] = 60 * 60
    USER_XP = "gam:xp:{user_id}"                                # SET integer (mirror)
    USER_XP_TTL: Final[int] = 5 * 60
    UNLOCK_QUEUE = "gam:unlock_queue:{user_id}"                 # LIST (achievement_ids pending toast)
    UNLOCK_QUEUE_TTL: Final[int] = 60 * 60


# ─────────────────────────── LFG (Module 16) ───────────────────────────
class LFG:
    """Looking-For-Game broadcast — sorted set keyed by city.
    Score = UNIX timestamp of `expires_at`; ZREMRANGEBYSCORE used to GC expired entries."""
    ACTIVE_BY_CITY = "lfg:active:{city}"                        # ZSET — score=expires_at_unix, member=lfg_id
    ACTIVE_BY_CITY_TTL: Final[int] = 4 * 60 * 60                # safety TTL beyond max LFG window
    DETAIL = "lfg:detail:{lfg_id}"                              # JSON
    DETAIL_TTL: Final[int] = 4 * 60 * 60
    USER_ACTIVE = "lfg:user:{user_id}"                          # SET active lfg_id (one per user)
    USER_ACTIVE_TTL: Final[int] = 4 * 60 * 60
    INTERESTED = "lfg:interested:{lfg_id}"                      # SET of user_ids who tapped "I'm In"
    INTERESTED_TTL: Final[int] = 4 * 60 * 60


# ─────────────────────────── MISC ───────────────────────────
class MISC:
    """Feature flags, idempotency, AI rate-limits, locks."""
    FEATURE_FLAGS = "ff:flags"                                  # HASH key=flag_code, value=JSON config
    FEATURE_FLAGS_TTL = TTL_FOREVER
    FEATURE_FLAGS_VERSION = "ff:version"                        # INCR on update — clients use to bust cache
    FEATURE_FLAGS_VERSION_TTL = TTL_FOREVER
    IDEMPOTENCY = "idem:{key}"                                  # SET (write-once, response cached)
    IDEMPOTENCY_TTL: Final[int] = 24 * 60 * 60
    AI_CHAT_QUOTA = "ai:chat:quota:{user_id}:{date}"            # INCR + EXPIRE; daily reset
    AI_CHAT_QUOTA_TTL: Final[int] = 36 * 60 * 60
    AI_BRIEF_RATELIMIT = "ai:brief:rl:{user_id}"
    AI_BRIEF_RATELIMIT_TTL: Final[int] = 60
    DISTRIBUTED_LOCK = "lock:{name}"                            # SETNX
    DISTRIBUTED_LOCK_TTL: Final[int] = 30
    HEALTH = "health:check"
    HEALTH_TTL: Final[int] = 30


# ─────────────────────────── PUBSUB CHANNELS ───────────────────────────
class PUBSUB:
    """Pub/sub channels — never expire; consumed by WebSocket gateways and Celery beat tasks."""
    MATCH_LIVE = "ps:match:live:{match_id}"                     # event broadcast to match viewers
    LFG_NEW = "ps:lfg:new:{city}"                               # new LFG broadcast in a city
    NOTIFICATION_USER = "ps:notif:user:{user_id}"               # personal push
    FEATURE_FLAG_UPDATED = "ps:ff:updated"                      # bust client caches on flag change
    LEADERBOARD_TICK = "ps:lb:tick"                             # nightly leaderboard refresh
    BROADCAST_VIEWER_COUNT = "ps:match:viewers:{match_id}"      # viewer count for HUD


__all__ = ["TTL_FOREVER", "AUTH", "USER", "MATCH", "TURF", "VIDEO",
           "SOCIAL", "GAMIFICATION", "LFG", "MISC", "PUBSUB"]
