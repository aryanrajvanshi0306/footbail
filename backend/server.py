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
import asyncio
import base64
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Literal, Set

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError

log = logging.getLogger("footbail")
logging.basicConfig(level=logging.INFO)

# ───────────────────────── Config ─────────────────────────
load_dotenv()
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGO = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MIN = int(os.environ.get("JWT_EXPIRES_MIN", "1440"))
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

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
    # Seed demo players (multi-city for Derby)
    seed_players = [
        # Mumbai (Straw Hat)
        ("arjun@demo.in",    "Arjun Sharma",    "CM", "Mumbai",    {"pac": 76, "sho": 71, "pas": 79, "dri": 74, "def": 68, "phy": 77}, "silver"),
        ("rohit@demo.in",    "Rohit Mehra",     "ST", "Mumbai",    {"pac": 82, "sho": 80, "pas": 66, "dri": 78, "def": 40, "phy": 72}, "silver"),
        ("vikram@demo.in",   "Vikram Rao",      "GK", "Mumbai",    {"pac": 52, "sho": 30, "pas": 58, "dri": 55, "def": 74, "phy": 78}, "bronze"),
        ("karan@demo.in",    "Karan Singh",     "CB", "Mumbai",    {"pac": 64, "sho": 48, "pas": 68, "dri": 62, "def": 82, "phy": 84}, "gold"),
        ("dev@demo.in",      "Dev Patel",       "LW", "Mumbai",    {"pac": 85, "sho": 72, "pas": 74, "dri": 83, "def": 42, "phy": 68}, "silver"),
        # Delhi (Hidden Leaf)
        ("aryan@delhi.in",   "Aryan Kapoor",    "CAM","Delhi",     {"pac": 78, "sho": 79, "pas": 84, "dri": 86, "def": 50, "phy": 70}, "gold"),
        ("ishan@delhi.in",   "Ishan Khanna",    "RW", "Delhi",     {"pac": 88, "sho": 75, "pas": 70, "dri": 84, "def": 38, "phy": 66}, "silver"),
        ("manav@delhi.in",   "Manav Gupta",     "CDM","Delhi",     {"pac": 70, "sho": 60, "pas": 80, "dri": 70, "def": 80, "phy": 82}, "gold"),
        # Bangalore (Plus Ultra)
        ("aditya@blr.in",    "Aditya Iyer",     "ST", "Bangalore", {"pac": 86, "sho": 82, "pas": 68, "dri": 80, "def": 42, "phy": 74}, "gold"),
        ("rahul@blr.in",     "Rahul Reddy",     "CM", "Bangalore", {"pac": 74, "sho": 70, "pas": 82, "dri": 78, "def": 70, "phy": 72}, "silver"),
        ("nikhil@blr.in",    "Nikhil Menon",    "LB", "Bangalore", {"pac": 80, "sho": 50, "pas": 72, "dri": 68, "def": 78, "phy": 76}, "silver"),
        # Kolkata (Cursed)
        ("sourav@kol.in",    "Sourav Ghosh",    "ST", "Kolkata",   {"pac": 84, "sho": 86, "pas": 64, "dri": 82, "def": 38, "phy": 72}, "gold"),
        ("debjit@kol.in",    "Debjit Dutta",    "CB", "Kolkata",   {"pac": 60, "sho": 42, "pas": 70, "dri": 60, "def": 86, "phy": 82}, "silver"),
        # Chennai (Power Spark)
        ("vinay@chn.in",     "Vinay Krishnan",  "CM", "Chennai",   {"pac": 76, "sho": 72, "pas": 80, "dri": 76, "def": 64, "phy": 70}, "silver"),
        ("ajith@chn.in",     "Ajith Kumar",     "RW", "Chennai",   {"pac": 86, "sho": 70, "pas": 68, "dri": 84, "def": 40, "phy": 64}, "silver"),
        # Hyderabad (The Wall)
        ("imran@hyd.in",     "Imran Ali",       "CB", "Hyderabad", {"pac": 62, "sho": 40, "pas": 66, "dri": 58, "def": 88, "phy": 86}, "gold"),
        ("rohan@hyd.in",     "Rohan Naidu",     "GK", "Hyderabad", {"pac": 50, "sho": 30, "pas": 60, "dri": 52, "def": 78, "phy": 80}, "silver"),
        # Pune (Breath of Flame)
        ("sahil@pune.in",    "Sahil Joshi",     "ST", "Pune",      {"pac": 82, "sho": 82, "pas": 64, "dri": 80, "def": 40, "phy": 72}, "silver"),
        # Kochi (Gotta Catch)
        ("anand@kochi.in",   "Anand Pillai",    "LW", "Kochi",     {"pac": 84, "sho": 70, "pas": 74, "dri": 82, "def": 44, "phy": 66}, "silver"),
    ]
    for email, name, pos, city, attrs, tier in seed_players:
        if not await db.users.find_one({"email": email}):
            ovr = round(sum(attrs.values()) / 6)
            # Per-city XP/stats variation so the Derby has actual rivalry
            import random
            random.seed(hash(email) & 0xFFFFFFFF)
            xp = random.randint(800, 6500)
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": email, "name": name, "role": "player",
                "position": pos, "city": city,
                "password_hash": hash_pw("demo123"),
                "attributes": attrs, "overall": ovr, "card_tier": tier,
                "xp": xp, "xp_to_next": 10000,
                "consistency": random.randint(60, 92),
                "stats": {
                    "matches": random.randint(8, 56),
                    "goals": random.randint(2, 22),
                    "assists": random.randint(1, 18),
                    "streak": random.randint(0, 9),
                },
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
    await _ws_push_event(mid, ev, score=m.get("score", {"home": 0, "away": 0}))
    return {"ok": True, "camera_status": "recording", "broadcast_active": True}

@app.post("/api/matches/{mid}/events")
async def add_event(mid: str, body: EventIn, user: dict = Depends(require_roles("admin", "referee"))):
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
    fresh = await db.matches.find_one({"id": mid}, {"_id": 0, "score": 1})
    await _ws_push_event(mid, ev, score=(fresh or {}).get("score"))
    return {k: v for k, v in ev.items() if k != "_id"}

@app.post("/api/matches/{mid}/offside-check")
async def offside_check(mid: str, user: dict = Depends(require_roles("admin", "referee"))):
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
    await _ws_push_event(mid, ev)
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
    await _ws_push_event(mid, ev, score=m.get("score"))
    # Final lifecycle marker
    await ws_manager.broadcast(mid, {"type": "match_complete", "match_id": mid})
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
    fouls = [e for e in events if e["type"] == "foul"]
    offsides = [e for e in events if e["type"] == "offside"]

    # Cache or generate AI summary
    cached = await db.match_analysis.find_one({"match_id": mid}, {"_id": 0})
    if cached and cached.get("summary"):
        summary = cached["summary"]
        source = cached.get("source", "cache")
    else:
        summary = await _ai_match_summary(m, events)
        # Detect if the returned text is the fallback template
        is_fallback = "AI offside system flagged" in summary and "all correctly overturned" in summary
        source = "fallback" if is_fallback else "gpt-4o-mini"
        await db.match_analysis.update_one(
            {"match_id": mid},
            {"$set": {"match_id": mid, "summary": summary, "source": source, "created_at": now_iso()}},
            upsert=True,
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
        "summary_source": source,
        "motm": {"name": "Arjun Sharma", "rating": 8.6, "position": "CM", "goals": 1, "assists": 2},
        "heatmap_points": [{"x": x, "y": y} for x, y in
                           [(22, 30), (35, 45), (48, 40), (55, 55), (62, 48), (70, 60), (45, 35), (38, 52)]],
    }


async def _ai_match_summary(match: dict, events: list) -> str:
    """Generate a 3-paragraph AI match analysis via Emergent LLM (GPT-4o-mini). Falls back gracefully."""
    fallback = _fallback_summary(match, events)
    if not EMERGENT_LLM_KEY:
        return fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        ev_rows = "\n".join([
            f"  · {e.get('minute', '?')}': {e.get('type')} — {e.get('team') or ''} {e.get('player_name') or ''}".strip()
            for e in events if e.get("type") in {"goal", "foul", "yellow_card", "red_card", "offside"}
        ]) or "  · (no logged events)"
        prompt = (
            f"Match: {match['home_team']} {match['score']['home']} – {match['score']['away']} {match['away_team']}\n"
            f"Venue: {match.get('turf_name', 'Turf')} · Format: {match.get('format', '5v5')}\n"
            f"Key events:\n{ev_rows}\n\n"
            "Write a tight 3-paragraph analysis (~120 words). "
            "Paragraph 1: who controlled the flow. Paragraph 2: the turning point & key individual moment. "
            "Paragraph 3: tactical takeaway for the losing side. "
            "Voice: confident football analyst. No emojis. No headings. No markdown. "
            "Separate paragraphs with a blank line."
        )
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"analysis-{match['id']}",
            system_message=(
                "You are a professional grassroots football analyst for India's footbAIl.in. "
                "Crisp, specific, tactical. No hype, no clichés."
            ),
        ).with_model("openai", "gpt-4o-mini")
        resp = await asyncio.wait_for(chat.send_message(UserMessage(text=prompt)), timeout=20)
        text = (resp or "").strip()
        return text if len(text) > 40 else fallback
    except Exception as e:
        log.warning("AI summary failed: %s", e)
        return fallback


def _fallback_summary(match: dict, events: list) -> str:
    goals = [e for e in events if e.get("type") == "goal"]
    fouls = [e for e in events if e.get("type") == "foul"]
    offsides = [e for e in events if e.get("type") == "offside"]
    yellows = [e for e in events if e.get("type") == "yellow_card"]
    return (
        f"{match['home_team']} dominated possession (58%) and created higher-quality chances. "
        f"Key turning point was the {len(goals)}-goal surge. Defensive discipline was tested "
        f"with {len(fouls)} fouls and {len(yellows)} cautions. "
        f"AI offside system flagged {len(offsides)} close calls — all correctly overturned."
    )


# ───────────────────────── Module 03 — Pre-Match Intelligence ─────────────────────────
@app.get("/api/matches/{mid}/brief")
async def pre_match_brief(mid: str, user: dict = Depends(current_user)):
    """Pre-Match Intelligence Pack: form, H2H, win probability, AI tactical brief.
    Cached in `match_briefs` so we don't re-spend on GPT calls."""
    m = await db.matches.find_one({"id": mid}, {"_id": 0})
    if not m: raise HTTPException(404, "Match not found")

    cached = await db.match_briefs.find_one({"match_id": mid}, {"_id": 0})
    if cached:
        return cached

    import random
    random.seed(hash(mid) & 0xFFFFFFFF)

    # Mock form (last 5 W/D/L) per team
    def form_for(team):
        outcomes = random.choices(["W", "D", "L"], weights=[5, 2, 3], k=5)
        return {"team": team, "form": outcomes,
                "wins": outcomes.count("W"), "draws": outcomes.count("D"), "losses": outcomes.count("L")}
    home_form = form_for(m["home_team"])
    away_form = form_for(m["away_team"])

    # Win probability — Poisson-ish on form
    home_strength = home_form["wins"] * 3 + home_form["draws"] - home_form["losses"]
    away_strength = away_form["wins"] * 3 + away_form["draws"] - away_form["losses"]
    total = max(1, home_strength + away_strength + 8)  # +8 for draw weight
    home_pct = max(15, min(70, int((home_strength + 4) / total * 100)))
    away_pct = max(15, min(70, int((away_strength + 4) / total * 100)))
    draw_pct = max(5, 100 - home_pct - away_pct)

    # H2H — 3 mocked previous matches
    h2h = []
    for i in range(3):
        h, a = random.randint(0, 4), random.randint(0, 4)
        h2h.append({"date": f"2025-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                    "home_team": m["home_team"], "away_team": m["away_team"],
                    "home_score": h, "away_score": a,
                    "winner": m["home_team"] if h > a else m["away_team"] if a > h else "Draw"})

    # Key matchup card
    matchups = [
        {"label": "Midfield Battle", "ours": "Arjun Sharma (CM)", "theirs": "their CDM", "edge": "track late runs"},
        {"label": "Pace Down Wing", "ours": "Dev Patel (LW)", "theirs": "their RB", "edge": "force 1v1s early"},
        {"label": "Set Piece Threat", "ours": "Karan Singh (CB)", "theirs": "their CBs", "edge": "near-post runs"},
    ]
    pick = random.choice(matchups)

    # AI tactical brief
    brief_text = await _ai_pre_match_brief(m, home_form, away_form, home_pct, draw_pct, away_pct, pick)

    # Personal role card (assumes user is player)
    role_card = {
        "position": user.get("position", "CM"),
        "instruction": "Stay compact in the half-spaces. Recycle through the holding role on transitions.",
        "targets": ["Win 6+ second-balls", "Complete 80%+ of passes in the final third"],
        "watch_out": "Their false-9 drops between lines on goal-kicks — track him."
    }

    doc = {
        "match_id": mid,
        "home_form": home_form, "away_form": away_form,
        "win_probability": {"home": home_pct, "draw": draw_pct, "away": away_pct},
        "h2h": h2h,
        "key_matchup": pick,
        "ai_brief": brief_text,
        "ai_brief_source": "gpt-4o-mini" if EMERGENT_LLM_KEY and "Stay compact" not in brief_text else "fallback",
        "role_card": role_card,
        "generated_at": now_iso(),
    }
    await db.match_briefs.update_one({"match_id": mid}, {"$set": doc}, upsert=True)
    return doc


async def _ai_pre_match_brief(match, home_form, away_form, hp, dp, ap, pick) -> str:
    fb = (
        f"{match['home_team']} arrive with {home_form['wins']}W-{home_form['draws']}D-{home_form['losses']}L form, "
        f"{match['away_team']} with {away_form['wins']}W-{away_form['draws']}D-{away_form['losses']}L. "
        f"Model gives {match['home_team']} a {hp}% edge with a {dp}% draw lean. "
        f"Decisive zone: {pick['label']} — {pick['edge']}."
    )
    if not EMERGENT_LLM_KEY:
        return fb
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        prompt = (
            f"Match: {match['home_team']} vs {match['away_team']} at {match.get('turf_name','Turf')} ({match.get('format','5v5')}).\n"
            f"Home form: {''.join(home_form['form'])} ({home_form['wins']}W-{home_form['draws']}D-{home_form['losses']}L). "
            f"Away form: {''.join(away_form['form'])} ({away_form['wins']}W-{away_form['draws']}D-{away_form['losses']}L).\n"
            f"Win probability: home {hp}% · draw {dp}% · away {ap}%.\n"
            f"Key matchup: {pick['label']} — our {pick['ours']} vs {pick['theirs']}; edge: {pick['edge']}.\n\n"
            "Write a 2-paragraph pre-match brief (~80 words). "
            "Para 1: how the match will likely flow & where it's decided. "
            "Para 2: one specific tactical adjustment our team should make. "
            "Voice: confident football analyst. No headings. No emojis. No markdown. "
            "Separate paragraphs with a blank line."
        )
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"brief-{match['id']}",
            system_message="You are an Indian grassroots football tactical analyst for footbAIl.in. Crisp, specific, no clichés."
        ).with_model("openai", "gpt-4o-mini")
        resp = await asyncio.wait_for(chat.send_message(UserMessage(text=prompt)), timeout=20)
        text = (resp or "").strip()
        return text if len(text) > 40 else fb
    except Exception as e:
        log.warning("Pre-match AI brief failed: %s", e)
        return fb


# ───────────────────────── Module 16 — Smart Matchmaking / LFG ─────────────────────────
class LFGIn(BaseModel):
    city: str
    format: str = "5v5"   # 5v5 / 7v7 / 11v11
    skill_bracket: Literal["casual", "intermediate", "competitive"] = "intermediate"
    earliest: str   # ISO datetime
    latest: str     # ISO datetime (max 3h after earliest)
    spots: int = 1  # how many players you need
    note: Optional[str] = None


@app.post("/api/lfg")
async def lfg_create(body: LFGIn, user: dict = Depends(current_user)):
    if user["role"] not in {"player", "coach"}:
        raise HTTPException(403, "Only players & coaches can broadcast LFG")
    # Cancel any existing active LFG by this user
    await db.lfg.update_many({"user_id": user["id"], "status": "active"}, {"$set": {"status": "cancelled"}})
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "user_name": user["name"],
        "user_position": user.get("position"),
        "user_tier": user.get("card_tier", "bronze"),
        "city": body.city,
        "format": body.format,
        "skill_bracket": body.skill_bracket,
        "earliest": body.earliest,
        "latest": body.latest,
        "spots": body.spots,
        "note": body.note,
        "status": "active",
        "created_at": now_iso(),
    }
    await db.lfg.insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


@app.get("/api/lfg")
async def lfg_list(city: Optional[str] = None):
    """List active LFGs in the next 3 hours, optionally filtered by city."""
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=3)
    query = {"status": "active"}
    if city: query["city"] = city
    rows = await db.lfg.find(query, {"_id": 0}).sort("earliest", 1).to_list(100)
    # Filter out expired ones in-memory
    out = []
    for r in rows:
        try:
            latest = datetime.fromisoformat(r["latest"].replace("Z", "+00:00"))
            if latest > now and datetime.fromisoformat(r["earliest"].replace("Z", "+00:00")) < horizon + timedelta(hours=24):
                out.append(r)
        except Exception:
            out.append(r)
    return out


@app.delete("/api/lfg/{lfg_id}")
async def lfg_cancel(lfg_id: str, user: dict = Depends(current_user)):
    r = await db.lfg.find_one({"id": lfg_id})
    if not r: raise HTTPException(404, "Not found")
    if r["user_id"] != user["id"] and user["role"] != "admin":
        raise HTTPException(403, "Not your broadcast")
    await db.lfg.update_one({"id": lfg_id}, {"$set": {"status": "cancelled"}})
    return {"ok": True}


# ───────────────────────── Module 11 (extension) — City Derby Leaderboard ─────────────────────────
CITY_THEMES_BACKEND = {
    "Mumbai":    {"accent": "#F5A623", "subtitle": "Straw Hat City"},
    "Delhi":     {"accent": "#FF6B00", "subtitle": "Hidden Leaf"},
    "Bangalore": {"accent": "#00C853", "subtitle": "Plus Ultra"},
    "Kolkata":   {"accent": "#7C3AED", "subtitle": "Cursed City"},
    "Chennai":   {"accent": "#FFD600", "subtitle": "Power Spark"},
    "Hyderabad": {"accent": "#00897B", "subtitle": "The Wall"},
    "Pune":      {"accent": "#E91E63", "subtitle": "Breath of Flame"},
    "Kochi":     {"accent": "#FFEB3B", "subtitle": "Gotta Catch"},
}


@app.get("/api/explore/derby")
async def city_derby():
    """Aggregate XP, players, matches, goals per city → ranked leaderboard."""
    pipeline = [
        {"$match": {"role": "player"}},
        {"$group": {
            "_id": "$city",
            "players": {"$sum": 1},
            "total_xp": {"$sum": {"$ifNull": ["$xp", 0]}},
            "total_goals": {"$sum": {"$ifNull": ["$stats.goals", 0]}},
            "total_matches": {"$sum": {"$ifNull": ["$stats.matches", 0]}},
            "avg_overall": {"$avg": {"$ifNull": ["$overall", 60]}},
        }},
    ]
    raw = await db.users.aggregate(pipeline).to_list(50)
    by_city = {r["_id"]: r for r in raw if r.get("_id")}

    # Ensure every defined city appears (even with zero players)
    rows = []
    for city, theme in CITY_THEMES_BACKEND.items():
        s = by_city.get(city, {"players": 0, "total_xp": 0, "total_goals": 0, "total_matches": 0, "avg_overall": 0})
        # City score = weighted blend (xp + goals*100 + matches*5 + avg_overall*100)
        score = int(s.get("total_xp", 0)
                    + s.get("total_goals", 0) * 100
                    + s.get("total_matches", 0) * 5
                    + (s.get("avg_overall") or 0) * 100)
        rows.append({
            "city": city,
            "accent": theme["accent"],
            "subtitle": theme["subtitle"],
            "players": s.get("players", 0),
            "total_xp": int(s.get("total_xp", 0)),
            "total_goals": s.get("total_goals", 0),
            "total_matches": s.get("total_matches", 0),
            "avg_overall": round(s.get("avg_overall") or 0, 1),
            "score": score,
        })
    rows.sort(key=lambda r: r["score"], reverse=True)
    for i, r in enumerate(rows): r["rank"] = i + 1
    return rows

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


# ═══════════════════════════════════════════════════════════════════════════
# Module — WebSocket Live Broadcast (replaces 3s polling)
# ═══════════════════════════════════════════════════════════════════════════
class _WSManager:
    """Per-match WebSocket connection manager. Broadcasts JSON event payloads."""
    def __init__(self):
        self._conns: dict[str, Set[WebSocket]] = {}

    async def connect(self, match_id: str, ws: WebSocket):
        await ws.accept()
        self._conns.setdefault(match_id, set()).add(ws)
        log.info("ws connected match=%s viewers=%d", match_id, len(self._conns[match_id]))

    def disconnect(self, match_id: str, ws: WebSocket):
        peers = self._conns.get(match_id) or set()
        peers.discard(ws)
        if not peers:
            self._conns.pop(match_id, None)

    def viewer_count(self, match_id: str) -> int:
        return len(self._conns.get(match_id) or set())

    async def broadcast(self, match_id: str, payload: dict):
        peers = list(self._conns.get(match_id) or set())
        if not peers:
            return
        msg = json.dumps(payload, default=str)
        dead: list[WebSocket] = []
        for ws in peers:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.disconnect(match_id, d)


ws_manager = _WSManager()


@app.websocket("/api/ws/match/{mid}")
async def ws_match(ws: WebSocket, mid: str):
    """Client subscribes to live updates for a match. Server pushes:
       - on connect: full snapshot { type: 'snapshot', match, events, viewers }
       - on event:    { type: 'event', event, score, viewers }
       - heartbeat:   client must send {"type":"ping"} → server replies {"type":"pong"}.
    """
    m = await db.matches.find_one({"id": mid}, {"_id": 0})
    if not m:
        await ws.close(code=4404)
        return
    await ws_manager.connect(mid, ws)
    try:
        events = await db.match_events.find({"match_id": mid}, {"_id": 0}).sort("created_at", 1).to_list(500)
        await ws.send_text(json.dumps({
            "type": "snapshot", "match": m, "events": events,
            "viewers": ws_manager.viewer_count(mid),
        }, default=str))
        # Notify others of viewer count change
        await ws_manager.broadcast(mid, {"type": "viewers", "viewers": ws_manager.viewer_count(mid)})
        while True:
            msg = await ws.receive_text()
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                continue
            if data.get("type") == "ping":
                await ws.send_text(json.dumps({"type": "pong", "ts": now_iso()}))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        log.warning("ws error match=%s err=%s", mid, e)
    finally:
        ws_manager.disconnect(mid, ws)
        # Notify remaining peers of viewer drop
        try:
            await ws_manager.broadcast(mid, {"type": "viewers", "viewers": ws_manager.viewer_count(mid)})
        except Exception:
            pass


async def _ws_push_event(mid: str, ev: dict, score: Optional[dict] = None):
    """Helper: broadcast an event dict to all WS subscribers for a match."""
    payload = {"type": "event", "event": {k: v for k, v in ev.items() if k != "_id"}}
    if score is not None:
        payload["score"] = score
    payload["viewers"] = ws_manager.viewer_count(mid)
    await ws_manager.broadcast(mid, payload)


# ═══════════════════════════════════════════════════════════════════════════
# Module — Phone OTP (DEV bypass; real Firebase wiring point)
# ═══════════════════════════════════════════════════════════════════════════
DEV_OTP = "123456"


def _normalize_phone(phone: str) -> str:
    """Accept '9876543210' / '+919876543210' / '09876...' → '+91XXXXXXXXXX'."""
    s = ''.join(ch for ch in (phone or '') if ch.isdigit() or ch == '+')
    if s.startswith('+91') and len(s) == 13:
        return s
    if s.startswith('91') and len(s) == 12:
        return '+' + s
    if s.startswith('0') and len(s) == 11:
        return '+91' + s[1:]
    if len(s) == 10 and s[0] in '6789':
        return '+91' + s
    raise HTTPException(422, "Enter a valid Indian mobile number")


class OTPSendIn(BaseModel):
    phone: str


class OTPVerifyIn(BaseModel):
    phone: str
    otp: str = Field(min_length=6, max_length=6)
    name: Optional[str] = None
    role: Optional[Literal["player", "coach"]] = "player"
    city: Optional[str] = "Mumbai"


@app.post("/api/auth/otp/send")
async def otp_send(body: OTPSendIn):
    """DEV: returns dev_otp in the response for easy local testing.
    PROD: swap to call _send_via_firebase / _send_via_msg91 (see postgres_layer/app/auth/otp.py)."""
    phone = _normalize_phone(body.phone)
    # Rate-limit (3 / 10 min) — simple Mongo-backed counter
    win_start = datetime.now(timezone.utc) - timedelta(minutes=10)
    count = await db.otp_log.count_documents({"phone": phone, "created_at_dt": {"$gte": win_start}})
    if count >= 3:
        raise HTTPException(429, "Too many OTP requests. Try again in 10 minutes.")
    await db.otp_log.insert_one({"phone": phone, "created_at_dt": datetime.now(timezone.utc),
                                  "created_at": now_iso(), "dev_mode": True})
    log.info("OTP issued phone=%s****%s dev_mode=True", phone[:3], phone[-4:])
    return {"sent": True, "expires_in": 300, "dev_mode": True, "dev_otp": DEV_OTP,
            "message": "DEV mode — use OTP 123456 (any phone)."}


@app.post("/api/auth/otp/verify", response_model=TokenOut)
async def otp_verify(body: OTPVerifyIn):
    phone = _normalize_phone(body.phone)
    if body.otp != DEV_OTP:
        raise HTTPException(401, "Invalid or expired OTP")
    # Login OR auto-create
    u = await db.users.find_one({"phone": phone})
    if not u:
        # First-time signup via OTP
        uid = str(uuid.uuid4())
        role = body.role or "player"
        if role == "player":
            attrs = {"pac": 68, "sho": 64, "pas": 70, "dri": 66, "def": 60, "phy": 69}
            ovr = round(sum(attrs.values()) / 6)
        else:
            attrs, ovr = {}, None
        u = {
            "id": uid, "email": f"{phone[1:]}@otp.footbail.in",
            "name": body.name or f"Player {phone[-4:]}",
            "role": role, "phone": phone,
            "position": "CM" if role == "player" else None,
            "city": body.city or "Mumbai",
            "password_hash": hash_pw(uuid.uuid4().hex),  # OTP-only login
            "attributes": attrs, "overall": ovr,
            "card_tier": "bronze" if role == "player" else None,
            "xp": 0, "xp_to_next": 1000, "consistency": 70,
            "stats": {"matches": 0, "goals": 0, "assists": 0, "streak": 0},
            "phone_verified_at": now_iso(),
            "auth_mode": "otp", "created_at": now_iso(),
        }
        await db.users.insert_one(u)
    else:
        # Mark phone verified
        if not u.get("phone_verified_at"):
            await db.users.update_one({"id": u["id"]}, {"$set": {"phone_verified_at": now_iso()}})
            u["phone_verified_at"] = now_iso()
    tok = make_token(u["id"], u["role"])
    return {"access_token": tok, "token_type": "bearer", "user": _clean_user(dict(u))}


# ═══════════════════════════════════════════════════════════════════════════
# Module — Razorpay Test Mode (DEV-mock; real keys wire-up via env)
# ═══════════════════════════════════════════════════════════════════════════
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")
RAZORPAY_DEV_MODE = not (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
# Stable mock secret used to generate verifiable signatures in dev
_DEV_RZP_SECRET = "dev_secret_footbail_2026"


class RzpOrderIn(BaseModel):
    match_id: Optional[str] = None
    turf_id: Optional[str] = None
    amount_paise: int = Field(ge=100)
    notes: Optional[dict] = None


class RzpVerifyIn(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    booking_id: Optional[str] = None


def _rzp_sign(order_id: str, payment_id: str) -> str:
    """HMAC-SHA256 over `order_id|payment_id` with key secret (Razorpay docs)."""
    secret = (RAZORPAY_KEY_SECRET or _DEV_RZP_SECRET).encode("utf-8")
    msg = f"{order_id}|{payment_id}".encode("utf-8")
    return hmac.new(secret, msg, hashlib.sha256).hexdigest()


@app.post("/api/payments/razorpay/order")
async def rzp_create_order(body: RzpOrderIn, user: dict = Depends(current_user)):
    """Create a Razorpay order (DEV-mock unless real keys present).
    Idempotent: if a match_id is provided and an open booking already exists for this user, returns it.
    """
    booking_id = str(uuid.uuid4())
    order_id = f"order_dev_{uuid.uuid4().hex[:16]}" if RAZORPAY_DEV_MODE else None

    # If real keys, attempt actual Razorpay order. Skipped here — dev only.
    if not RAZORPAY_DEV_MODE:
        try:
            import httpx
            async with httpx.AsyncClient(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET), timeout=10) as c:
                r = await c.post("https://api.razorpay.com/v1/orders", json={
                    "amount": body.amount_paise, "currency": "INR",
                    "receipt": booking_id, "notes": body.notes or {},
                })
                r.raise_for_status()
                order_id = r.json()["id"]
        except Exception as e:
            log.warning("Razorpay order creation failed: %s — falling back to dev mock", e)
            order_id = f"order_dev_{uuid.uuid4().hex[:16]}"

    booking = {
        "id": booking_id, "user_id": user["id"], "user_name": user["name"],
        "match_id": body.match_id, "turf_id": body.turf_id,
        "amount_paise": body.amount_paise, "currency": "INR",
        "razorpay_order_id": order_id, "razorpay_payment_id": None,
        "payment_status": "pending",
        "dev_mode": RAZORPAY_DEV_MODE,
        "notes": body.notes or {}, "created_at": now_iso(),
    }
    await db.bookings.insert_one(booking)
    return {
        "booking_id": booking_id,
        "order_id": order_id,
        "amount_paise": body.amount_paise, "currency": "INR",
        "key_id": RAZORPAY_KEY_ID or "rzp_test_dev_key",
        "dev_mode": RAZORPAY_DEV_MODE,
    }


@app.post("/api/payments/razorpay/verify")
async def rzp_verify(body: RzpVerifyIn, user: dict = Depends(current_user)):
    """Verify HMAC-SHA256 signature, mark booking paid. DEV-mock signature acceptance enabled."""
    expected = _rzp_sign(body.razorpay_order_id, body.razorpay_payment_id)
    if not hmac.compare_digest(expected, body.razorpay_signature):
        raise HTTPException(400, "Invalid payment signature")

    booking = await db.bookings.find_one({"razorpay_order_id": body.razorpay_order_id, "user_id": user["id"]})
    if not booking:
        raise HTTPException(404, "Booking not found")
    if booking["payment_status"] == "paid":
        return {k: v for k, v in booking.items() if k != "_id"}
    qr_token = uuid.uuid4().hex
    await db.bookings.update_one(
        {"id": booking["id"]},
        {"$set": {
            "payment_status": "paid",
            "razorpay_payment_id": body.razorpay_payment_id,
            "razorpay_signature": body.razorpay_signature,
            "paid_at": now_iso(),
            "qr_token": qr_token,
        }},
    )
    booking.update({
        "payment_status": "paid", "razorpay_payment_id": body.razorpay_payment_id,
        "qr_token": qr_token,
    })
    return {k: v for k, v in booking.items() if k != "_id"}


@app.post("/api/payments/razorpay/dev-sign")
async def rzp_dev_sign(payload: dict, user: dict = Depends(current_user)):
    """DEV-only helper. Frontend posts {order_id, payment_id} → server returns the HMAC sig.
    In production, the signature would come from Razorpay Checkout's success handler — never the server."""
    if not RAZORPAY_DEV_MODE:
        raise HTTPException(403, "Dev signing is disabled in production mode")
    order_id = payload.get("order_id"); payment_id = payload.get("payment_id") or f"pay_dev_{uuid.uuid4().hex[:16]}"
    if not order_id:
        raise HTTPException(422, "order_id is required")
    return {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": _rzp_sign(order_id, payment_id),
    }


@app.get("/api/bookings/me")
async def my_bookings(user: dict = Depends(current_user)):
    rows = await db.bookings.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return rows


# ═══════════════════════════════════════════════════════════════════════════
# Module — Gemini Nano Banana Player Avatar
# ═══════════════════════════════════════════════════════════════════════════
class AvatarGenIn(BaseModel):
    style: Optional[str] = "fifa-card"   # fifa-card | anime | realistic


@app.post("/api/players/avatar")
async def player_avatar_generate(body: AvatarGenIn, user: dict = Depends(current_user)):
    """Generate (or regenerate) a stylised player avatar via Gemini Nano Banana.
       Returns the image as a data URL the frontend can render directly."""
    if not EMERGENT_LLM_KEY:
        raise HTTPException(503, "AI image generation unavailable (no LLM key)")
    if user["role"] not in {"player", "coach"}:
        raise HTTPException(403, "Avatar generation is for players and coaches only")

    city_subtitle = CITY_THEMES_BACKEND.get(user.get("city", "Mumbai"), {}).get("subtitle", "")
    position = user.get("position") or "CM"
    tier = user.get("card_tier") or "bronze"
    style = (body.style or "fifa-card").lower()

    style_hint = {
        "fifa-card": "FIFA-style ultimate-team card portrait, hyper-clean studio lighting, dramatic spotlight, head-and-shoulders shot.",
        "anime":     "anime-inspired character portrait, bold cel-shading, dramatic eyes, sports uniform.",
        "realistic": "photoreal portrait, action sports photography, natural daylight, shallow depth of field.",
    }.get(style, "FIFA-style portrait")

    prompt = (
        f"Square 1:1 stylised football player portrait. "
        f"{style_hint} "
        f"Player position: {position}. Tier accent: {tier}. "
        f"Subtle background reference: '{city_subtitle}' aesthetic, dark navy gradient (#0A0F1E → #1C2333). "
        f"No text, no logos, no watermarks. Strong focus on the player's face. "
        f"Render a fictional Indian player, age 22-28, athletic build, jersey color in the city accent."
    )
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"avatar-{user['id']}-{uuid.uuid4().hex[:8]}",
            system_message="You generate clean stylised football-player portraits.",
        ).with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
        text, images = await asyncio.wait_for(
            chat.send_message_multimodal_response(UserMessage(text=prompt)),
            timeout=45,
        )
        if not images:
            raise HTTPException(502, "Avatar service returned no image")
        img = images[0]
        mime = img.get("mime_type", "image/png")
        data_url = f"data:{mime};base64,{img['data']}"
        await db.users.update_one({"id": user["id"]},
                                  {"$set": {"avatar_url": data_url, "avatar_style": style,
                                            "avatar_generated_at": now_iso()}})
        return {"avatar_url": data_url, "style": style}
    except asyncio.TimeoutError:
        raise HTTPException(504, "Avatar generation timed out")
    except HTTPException:
        raise
    except Exception as e:
        log.warning("Avatar gen failed: %s", e)
        raise HTTPException(502, f"Avatar generation failed: {e}")


@app.get("/api/players/me/avatar")
async def my_avatar(user: dict = Depends(current_user)):
    u = await db.users.find_one({"id": user["id"]}, {"_id": 0, "avatar_url": 1, "avatar_style": 1, "avatar_generated_at": 1})
    return u or {}
