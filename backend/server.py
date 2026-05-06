"""
footbAIl.in — India's AI Football OS
Single-file FastAPI backend (MVP scaffold).

Roles:
  - player, coach    -> self-signup
  - admin            -> pre-seeded (admin@footbail.in / admin123)
  - turf_owner, referee -> admin creates manually
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError

# ───────────────────────── Config ─────────────────────────
load_dotenv()
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGO = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MIN = int(os.environ.get("JWT_EXPIRES_MIN", "1440"))
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

# ───────────────────────── DB & Auth ─────────────────────────
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def hash_pw(pw: str) -> str: return pwd_ctx.hash(pw)
def verify_pw(pw: str, h: str) -> bool: return pwd_ctx.verify(pw, h)

def now_iso() -> str: return datetime.now(timezone.utc).isoformat()

def make_token(uid: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MIN)
    return jwt.encode({"sub": uid, "role": role, "exp": exp}, JWT_SECRET, algorithm=JWT_ALGO)

async def current_user(token: Optional[str] = Depends(oauth2)) -> dict:
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except JWTError:
        raise HTTPException(401, "Invalid token")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(401, "User not found")
    return user

def require_roles(*roles):
    async def _inner(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(403, f"Requires role: {'/'.join(roles)}")
        return user
    return _inner

# ───────────────────────── Models ─────────────────────────
Role = Literal["player", "coach", "admin", "turf_owner", "referee"]

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)
    name: str
    role: Literal["player", "coach"]  # only these two can self-signup
    phone: Optional[str] = None
    position: Optional[str] = None   # Player: ST/CM/GK etc.
    city: Optional[str] = "Mumbai"

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserCreateAdmin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)
    name: str
    role: Literal["turf_owner", "referee"]
    phone: Optional[str] = None

class TurfIn(BaseModel):
    name: str
    city: str
    address: str
    price_per_slot: int = 120000  # paise
    owner_id: Optional[str] = None
    image: Optional[str] = None

class PostIn(BaseModel):
    content: str

class ReactIn(BaseModel):
    reaction: Literal["boot", "gloves", "whistle", "fire", "hundred"]

class MatchIn(BaseModel):
    home_team: str
    away_team: str
    turf_id: str
    scheduled_at: str            # ISO datetime
    referee_id: Optional[str] = None
    format: str = "5v5"
    notes: Optional[str] = None

class EventIn(BaseModel):
    type: Literal["kickoff", "foul", "goal", "yellow_card", "red_card", "offside", "substitution", "complete"]
    team: Optional[str] = None
    player_name: Optional[str] = None
    minute: Optional[int] = None
    notes: Optional[str] = None

# ───────────────────────── App ─────────────────────────
app = FastAPI(title="footbAIl API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────── Health ─────────────────────────
@app.get("/api/health")
async def health(): return {"status": "ok", "ts": now_iso()}

# ───────────────────────── Auth ─────────────────────────
def _clean_user(u: dict) -> dict:
    u.pop("_id", None); u.pop("password_hash", None); return u

@app.post("/api/auth/register", response_model=TokenOut)
async def register(body: RegisterIn):
    if await db.users.find_one({"email": body.email.lower()}):
        raise HTTPException(400, "Email already registered")
    uid = str(uuid.uuid4())
    # starter FIFA card stats for players
    if body.role == "player":
        attrs = {"pac": 68, "sho": 64, "pas": 70, "dri": 66, "def": 60, "phy": 69}
        ovr = round(sum(attrs.values()) / 6)
    else:
        attrs, ovr = {}, None
    user = {
        "id": uid,
        "email": body.email.lower(),
        "name": body.name,
        "role": body.role,
        "phone": body.phone,
        "position": body.position or ("CM" if body.role == "player" else None),
        "city": body.city or "Mumbai",
        "password_hash": hash_pw(body.password),
        "attributes": attrs,
        "overall": ovr,
        "card_tier": "bronze" if body.role == "player" else None,
        "xp": 0,
        "xp_to_next": 1000,
        "consistency": 72,
        "stats": {"matches": 0, "goals": 0, "assists": 0, "streak": 0},
        "created_at": now_iso(),
    }
    await db.users.insert_one(user)
    tok = make_token(uid, body.role)
    return {"access_token": tok, "token_type": "bearer", "user": _clean_user(dict(user))}

@app.post("/api/auth/login", response_model=TokenOut)
async def login(body: LoginIn):
    u = await db.users.find_one({"email": body.email.lower()})
    if not u or not verify_pw(body.password, u["password_hash"]):
        raise HTTPException(401, "Invalid email or password")
    tok = make_token(u["id"], u["role"])
    return {"access_token": tok, "token_type": "bearer", "user": _clean_user(dict(u))}

@app.get("/api/auth/me")
async def me(user: dict = Depends(current_user)): return user

# ───────────────────────── Admin ─────────────────────────
@app.post("/api/admin/seed")
async def seed():
    """Idempotent seed: creates admin + demo data."""
    # Admin
    if not await db.users.find_one({"email": "admin@footbail.in"}):
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": "admin@footbail.in",
            "name": "Platform Admin",
            "role": "admin",
            "password_hash": hash_pw("admin123"),
            "created_at": now_iso(),
        })
    # Seed demo players
    seed_players = [
        ("arjun@demo.in", "Arjun Sharma", "CM", {"pac": 76, "sho": 71, "pas": 79, "dri": 74, "def": 68, "phy": 77}, "silver"),
        ("rohit@demo.in", "Rohit Mehra", "ST", {"pac": 82, "sho": 80, "pas": 66, "dri": 78, "def": 40, "phy": 72}, "silver"),
        ("vikram@demo.in", "Vikram Rao", "GK", {"pac": 52, "sho": 30, "pas": 58, "dri": 55, "def": 74, "phy": 78}, "bronze"),
        ("karan@demo.in", "Karan Singh", "CB", {"pac": 64, "sho": 48, "pas": 68, "dri": 62, "def": 82, "phy": 84}, "gold"),
        ("dev@demo.in", "Dev Patel", "LW", {"pac": 85, "sho": 72, "pas": 74, "dri": 83, "def": 42, "phy": 68}, "silver"),
    ]
    for email, name, pos, attrs, tier in seed_players:
        if not await db.users.find_one({"email": email}):
            ovr = round(sum(attrs.values()) / 6)
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": email, "name": name, "role": "player",
                "position": pos, "city": "Mumbai",
                "password_hash": hash_pw("demo123"),
                "attributes": attrs, "overall": ovr, "card_tier": tier,
                "xp": 3420, "xp_to_next": 10000, "consistency": 82,
                "stats": {"matches": 47, "goals": 12, "assists": 23, "streak": 6},
                "created_at": now_iso(),
            })
    # Seed coaches
    for email, name in [("ravi@coach.in", "Coach Ravi Kumar"), ("suresh@coach.in", "Coach Suresh Nair")]:
        if not await db.users.find_one({"email": email}):
            await db.users.insert_one({
                "id": str(uuid.uuid4()), "email": email, "name": name, "role": "coach",
                "password_hash": hash_pw("demo123"),
                "bio": "10+ years, UEFA B licensed. Specializes in midfield tactics.",
                "rating": 4.8, "sessions": 156, "price_per_hour": 80000,
                "created_at": now_iso(),
            })
    # Seed turfs
    turfs = [
        ("Powai Turf Arena", "Mumbai", "Hiranandani Gardens, Powai"),
        ("Andheri Sports Hub", "Mumbai", "Lokhandwala Complex, Andheri West"),
        ("BKC Box Soccer", "Mumbai", "Bandra Kurla Complex"),
        ("Koramangala Kicks", "Bangalore", "5th Block, Koramangala"),
    ]
    for n, c, a in turfs:
        if not await db.turfs.find_one({"name": n}):
            await db.turfs.insert_one({
                "id": str(uuid.uuid4()), "name": n, "city": c, "address": a,
                "price_per_slot": 120000, "rating": 4.6,
                "image": "https://images.pexels.com/photos/17264600/pexels-photo-17264600.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
                "created_at": now_iso(),
            })
    # Seed posts
    if await db.posts.count_documents({}) == 0:
        players = await db.users.find({"role": "player"}, {"_id": 0}).to_list(10)
        sample_posts = [
            "Smashed a hat-trick at Powai last night 🔥 card upgrade incoming?",
            "Looking for 2 more at BKC tomorrow 7pm. 5v5, chill vibes.",
            "Who's watching the derby tonight? My money's on a 2-1 thriller.",
            "Finally hit gold tier. 18 months of grind paying off.",
            "Coach Ravi's new drill plan = certified chef kiss. Defense locked in.",
        ]
        for i, content in enumerate(sample_posts):
            p = players[i % len(players)] if players else None
            if p:
                await db.posts.insert_one({
                    "id": str(uuid.uuid4()),
                    "user_id": p["id"], "user_name": p["name"], "user_position": p.get("position"),
                    "user_tier": p.get("card_tier", "bronze"),
                    "content": content,
                    "reactions": {"boot": 0, "gloves": 0, "whistle": 0, "fire": 0, "hundred": 0},
                    "reacted_by": {},
                    "created_at": now_iso(),
                })
    # Seed matches
    if await db.matches.count_documents({}) == 0:
        turf_doc = await db.turfs.find_one({}, {"_id": 0})
        if turf_doc:
            for i, (h, a, status, offset_h) in enumerate([
                ("FC Powai", "Andheri United", "scheduled", 24),
                ("BKC Strikers", "Bandra Boys", "scheduled", 48),
                ("Mumbai XI", "Delhi Dragons", "complete", -72),
            ]):
                await db.matches.insert_one({
                    "id": str(uuid.uuid4()),
                    "home_team": h, "away_team": a,
                    "turf_id": turf_doc["id"], "turf_name": turf_doc["name"],
                    "scheduled_at": (datetime.now(timezone.utc) + timedelta(hours=offset_h)).isoformat(),
                    "status": status, "format": "5v5",
                    "score": {"home": 3 if status == "complete" else 0, "away": 2 if status == "complete" else 0},
                    "broadcast_active": False,
                    "created_at": now_iso(),
                })
    return {"seeded": True}

@app.post("/api/admin/create-user", response_model=TokenOut, dependencies=[Depends(require_roles("admin"))])
async def admin_create_user(body: UserCreateAdmin):
    """Admin manually creates turf_owner or referee."""
    if await db.users.find_one({"email": body.email.lower()}):
        raise HTTPException(400, "Email already exists")
    uid = str(uuid.uuid4())
    u = {
        "id": uid, "email": body.email.lower(), "name": body.name,
        "role": body.role, "phone": body.phone,
        "password_hash": hash_pw(body.password),
        "created_at": now_iso(),
    }
    if body.role == "referee":
        u.update({"cert_level": "AIFF Level 2", "experience_years": 3, "matches_officiated": 0, "rating": 4.5})
    await db.users.insert_one(u)
    tok = make_token(uid, body.role)
    return {"access_token": tok, "token_type": "bearer", "user": _clean_user(dict(u))}

@app.get("/api/admin/users", dependencies=[Depends(require_roles("admin"))])
async def admin_list_users(role: Optional[str] = None):
    q = {"role": role} if role else {}
    return await db.users.find(q, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(500)

@app.get("/api/admin/stats", dependencies=[Depends(require_roles("admin"))])
async def admin_stats():
    return {
        "players": await db.users.count_documents({"role": "player"}),
        "coaches": await db.users.count_documents({"role": "coach"}),
        "referees": await db.users.count_documents({"role": "referee"}),
        "turf_owners": await db.users.count_documents({"role": "turf_owner"}),
        "turfs": await db.turfs.count_documents({}),
        "matches_total": await db.matches.count_documents({}),
        "matches_live": await db.matches.count_documents({"status": "live"}),
        "matches_scheduled": await db.matches.count_documents({"status": "scheduled"}),
        "posts": await db.posts.count_documents({}),
    }

# ───────────────────────── Turfs ─────────────────────────
@app.get("/api/turfs")
async def list_turfs():
    return await db.turfs.find({}, {"_id": 0}).sort("name", 1).to_list(200)

@app.post("/api/turfs", dependencies=[Depends(require_roles("admin", "turf_owner"))])
async def create_turf(body: TurfIn, user: dict = Depends(current_user)):
    tid = str(uuid.uuid4())
    owner_id = body.owner_id or user["id"]
    doc = {"id": tid, "name": body.name, "city": body.city, "address": body.address,
           "price_per_slot": body.price_per_slot, "owner_id": owner_id,
           "image": body.image or "https://images.pexels.com/photos/17264600/pexels-photo-17264600.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
           "rating": 4.5, "created_at": now_iso()}
    await db.turfs.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}

# ───────────────────────── Posts / Feed ─────────────────────────
@app.get("/api/posts")
async def list_posts():
    return await db.posts.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)

@app.post("/api/posts")
async def create_post(body: PostIn, user: dict = Depends(current_user)):
    p = {"id": str(uuid.uuid4()),
         "user_id": user["id"], "user_name": user["name"],
         "user_position": user.get("position"), "user_tier": user.get("card_tier", "bronze"),
         "content": body.content,
         "reactions": {"boot": 0, "gloves": 0, "whistle": 0, "fire": 0, "hundred": 0},
         "reacted_by": {}, "created_at": now_iso()}
    await db.posts.insert_one(p)
    return {k: v for k, v in p.items() if k != "_id"}

@app.post("/api/posts/{post_id}/react")
async def react(post_id: str, body: ReactIn, user: dict = Depends(current_user)):
    post = await db.posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(404, "Post not found")
    reacted_by = post.get("reacted_by", {})
    prev = reacted_by.get(user["id"])
    reactions = post.get("reactions", {"boot": 0, "gloves": 0, "whistle": 0, "fire": 0, "hundred": 0})
    if prev == body.reaction:
        reactions[body.reaction] = max(0, reactions.get(body.reaction, 0) - 1)
        reacted_by.pop(user["id"], None)
    else:
        if prev:
            reactions[prev] = max(0, reactions.get(prev, 0) - 1)
        reactions[body.reaction] = reactions.get(body.reaction, 0) + 1
        reacted_by[user["id"]] = body.reaction
    await db.posts.update_one({"id": post_id}, {"$set": {"reactions": reactions, "reacted_by": reacted_by}})
    return {"reactions": reactions, "my_reaction": reacted_by.get(user["id"])}

# ───────────────────────── Matches ─────────────────────────
@app.get("/api/matches")
async def list_matches(status: Optional[str] = None):
    q = {"status": status} if status else {}
    return await db.matches.find(q, {"_id": 0}).sort("scheduled_at", 1).to_list(200)

@app.get("/api/matches/{mid}")
async def get_match(mid: str):
    m = await db.matches.find_one({"id": mid}, {"_id": 0})
    if not m: raise HTTPException(404, "Match not found")
    events = await db.match_events.find({"match_id": mid}, {"_id": 0}).sort("created_at", 1).to_list(500)
    m["events"] = events
    return m

@app.post("/api/matches")
async def create_match(body: MatchIn, user: dict = Depends(current_user)):
    turf = await db.turfs.find_one({"id": body.turf_id}, {"_id": 0})
    if not turf: raise HTTPException(404, "Turf not found")
    mid = str(uuid.uuid4())
    doc = {
        "id": mid,
        "home_team": body.home_team, "away_team": body.away_team,
        "turf_id": body.turf_id, "turf_name": turf["name"],
        "scheduled_at": body.scheduled_at,
        "status": "scheduled",
        "format": body.format, "notes": body.notes,
        "referee_id": body.referee_id,
        "creator_id": user["id"],
        "score": {"home": 0, "away": 0},
        "broadcast_active": False,
        "camera_status": "idle",
        "created_at": now_iso(),
    }
    await db.matches.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}

@app.post("/api/matches/{mid}/start")
async def start_match(mid: str, user: dict = Depends(require_roles("admin", "referee"))):
    """Starts the turf camera. Simulated."""
    m = await db.matches.find_one({"id": mid})
    if not m: raise HTTPException(404, "Match not found")
    await db.matches.update_one({"id": mid}, {"$set": {
        "status": "live", "broadcast_active": True, "camera_status": "recording",
        "started_at": now_iso(),
    }})
    ev = {"id": str(uuid.uuid4()), "match_id": mid, "type": "camera_on",
          "notes": "Turf camera started — live broadcast active",
          "minute": 0, "auto_detected": True, "created_at": now_iso()}
    await db.match_events.insert_one(ev)
    return {"ok": True, "camera_status": "recording", "broadcast_active": True}

@app.post("/api/matches/{mid}/events")
async def add_event(mid: str, body: EventIn, user: dict = Depends(current_user)):
    m = await db.matches.find_one({"id": mid})
    if not m: raise HTTPException(404, "Match not found")
    ev = {"id": str(uuid.uuid4()), "match_id": mid, **body.model_dump(),
          "auto_detected": False, "created_at": now_iso(),
          "logged_by": user["name"], "logged_by_role": user["role"]}
    await db.match_events.insert_one(ev)
    # Update score on goal
    if body.type == "goal" and body.team:
        update_key = "score.home" if body.team == m["home_team"] else "score.away"
        await db.matches.update_one({"id": mid}, {"$inc": {update_key: 1}})
    return {k: v for k, v in ev.items() if k != "_id"}

@app.post("/api/matches/{mid}/offside-check")
async def offside_check(mid: str, user: dict = Depends(current_user)):
    """Simulated AI offside detection — coin-flip whether it was offside."""
    import random
    is_offside = random.random() < 0.6
    ev = {"id": str(uuid.uuid4()), "match_id": mid,
          "type": "offside" if is_offside else "onside",
          "notes": "AI camera detection — offside line crossed by 0.42m" if is_offside
                   else "AI camera detection — attacker onside by 0.18m",
          "auto_detected": True, "confidence": round(random.uniform(0.82, 0.99), 2),
          "created_at": now_iso()}
    await db.match_events.insert_one(ev)
    return {k: v for k, v in ev.items() if k != "_id"}

@app.post("/api/matches/{mid}/complete")
async def complete_match(mid: str, user: dict = Depends(require_roles("admin", "referee"))):
    m = await db.matches.find_one({"id": mid})
    if not m: raise HTTPException(404, "Match not found")
    await db.matches.update_one({"id": mid}, {"$set": {
        "status": "complete", "broadcast_active": False,
        "camera_status": "stopped", "completed_at": now_iso(),
    }})
    ev = {"id": str(uuid.uuid4()), "match_id": mid, "type": "camera_off",
          "notes": "Match complete — camera recording stopped", "auto_detected": True,
          "created_at": now_iso()}
    await db.match_events.insert_one(ev)
    return {"ok": True, "status": "complete"}

@app.get("/api/matches/{mid}/broadcast")
async def broadcast_feed(mid: str):
    m = await db.matches.find_one({"id": mid}, {"_id": 0})
    if not m: raise HTTPException(404, "Match not found")
    events = await db.match_events.find({"match_id": mid}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"match": m, "events": events}

@app.get("/api/matches/{mid}/analysis")
async def analysis(mid: str):
    m = await db.matches.find_one({"id": mid}, {"_id": 0})
    if not m: raise HTTPException(404, "Match not found")
    events = await db.match_events.find({"match_id": mid}, {"_id": 0}).to_list(500)
    goals = [e for e in events if e["type"] == "goal"]
    fouls = [e for e in events if e["type"] == "foul"]
    offsides = [e for e in events if e["type"] == "offside"]
    yellows = [e for e in events if e["type"] == "yellow_card"]
    # Mock performance analysis text
    summary = (
        f"{m['home_team']} dominated possession (58%) and created higher-quality chances. "
        f"Key turning point was the {len(goals)}-goal surge. Defensive discipline was tested "
        f"with {len(fouls)} fouls and {len(yellows)} cautions. "
        f"AI offside system flagged {len(offsides)} close calls — all correctly overturned."
    )
    return {
        "match": m, "events": events,
        "stats": {
            "possession": {"home": 58, "away": 42},
            "shots": {"home": 11, "away": 7},
            "shots_on_target": {"home": 6, "away": 3},
            "passes": {"home": 312, "away": 241},
            "pass_accuracy": {"home": 84, "away": 77},
            "fouls": {"home": max(1, len(fouls)//2), "away": max(1, len(fouls)-len(fouls)//2)},
            "offsides": {"home": max(0, len(offsides)//2), "away": max(0, len(offsides)-len(offsides)//2)},
            "corners": {"home": 5, "away": 3},
        },
        "summary": summary,
        "motm": {"name": "Arjun Sharma", "rating": 8.6, "position": "CM", "goals": 1, "assists": 2},
        "heatmap_points": [{"x": x, "y": y} for x, y in
                           [(22, 30), (35, 45), (48, 40), (55, 55), (62, 48), (70, 60), (45, 35), (38, 52)]],
    }

# ───────────────────────── Explore (3x3) ─────────────────────────
@app.get("/api/explore/coaches")
async def explore_coaches():
    rows = await db.users.find({"role": "coach"}, {"_id": 0, "password_hash": 0}).to_list(50)
    return rows

@app.get("/api/explore/leaderboard")
async def leaderboard():
    rows = await db.users.find(
        {"role": "player"},
        {"_id": 0, "password_hash": 0}
    ).sort("overall", -1).to_list(50)
    return rows

@app.get("/api/explore/teams")
async def explore_teams():
    return [
        {"id": "t1", "name": "FC Powai", "city": "Mumbai", "members": 14, "trophies": 3, "logo_color": "#FF3B30"},
        {"id": "t2", "name": "Andheri United", "city": "Mumbai", "members": 18, "trophies": 2, "logo_color": "#007AFF"},
        {"id": "t3", "name": "BKC Strikers", "city": "Mumbai", "members": 12, "trophies": 5, "logo_color": "#E6FF00"},
        {"id": "t4", "name": "Bandra Boys", "city": "Mumbai", "members": 16, "trophies": 1, "logo_color": "#34C759"},
    ]

@app.get("/api/explore/partners")
async def partners():
    return [
        {"id": "p1", "name": "Nike India", "category": "Kit & Boots", "discount": "15% off"},
        {"id": "p2", "name": "Gatorade", "category": "Hydration", "discount": "Free with booking"},
        {"id": "p3", "name": "Decathlon", "category": "Equipment", "discount": "10% off"},
    ]

@app.get("/api/explore/drills")
async def drills():
    return [
        {"id": "d1", "title": "Cone Weave Sprint", "duration": "12 min", "difficulty": "Intermediate", "focus": "Dribbling"},
        {"id": "d2", "title": "Wall Pass Combo", "duration": "15 min", "difficulty": "Beginner", "focus": "Passing"},
        {"id": "d3", "title": "Press & Trap", "duration": "20 min", "difficulty": "Advanced", "focus": "Defending"},
    ]

@app.get("/api/explore/events")
async def events():
    return [
        {"id": "e1", "title": "Mumbai Monsoon Cup 2026", "date": "2026-07-14", "city": "Mumbai", "prize": "₹1,50,000"},
        {"id": "e2", "title": "Bangalore 5s Championship", "date": "2026-08-22", "city": "Bangalore", "prize": "₹80,000"},
    ]

@app.get("/api/explore/trophies")
async def trophies():
    return [
        {"id": "tr1", "name": "Hat-Trick Hero", "rarity": "Epic", "unlocked": True},
        {"id": "tr2", "name": "Clean Sheet King", "rarity": "Rare", "unlocked": True},
        {"id": "tr3", "name": "Century Club", "rarity": "Legendary", "unlocked": False},
        {"id": "tr4", "name": "Derby Destroyer", "rarity": "Rare", "unlocked": True},
    ]

@app.get("/api/explore/tournaments")
async def tournaments():
    return [
        {"id": "to1", "name": "Powai Premier League", "status": "Ongoing", "teams": 8, "matchday": 4},
        {"id": "to2", "name": "BKC Box Cup", "status": "Registration Open", "teams": 0, "matchday": 0},
    ]

@app.get("/api/explore/turfs")
async def explore_turfs():
    return await db.turfs.find({}, {"_id": 0}).to_list(100)
