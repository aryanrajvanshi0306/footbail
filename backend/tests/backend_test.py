"""
footbAIl backend tests — covers auth, RBAC, posts, matches pipeline,
explore endpoints, and admin seed/stats. Uses REACT_APP_BACKEND_URL.
"""
import os
import time
import uuid
import requests
import pytest

# ── Resolve BASE_URL from frontend .env (deployed preview URL) ──
def _read_env():
    p = "/app/frontend/.env"
    if os.path.exists(p):
        for line in open(p):
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip()
    return os.environ["REACT_APP_BACKEND_URL"]

BASE_URL = _read_env().rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@footbail.in", "password": "admin123"}
PLAYER = {"email": "arjun@demo.in", "password": "demo123"}
COACH = {"email": "ravi@coach.in", "password": "demo123"}


# ────────── Fixtures ──────────
@pytest.fixture(scope="session", autouse=True)
def seed_once():
    """Idempotent seed before any test."""
    r = requests.post(f"{API}/admin/seed", timeout=30)
    assert r.status_code == 200, r.text
    assert r.json().get("seeded") is True


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    data = r.json()
    assert "access_token" in data and data["token_type"] == "bearer"
    return data


@pytest.fixture(scope="session")
def admin_token():
    return _login(ADMIN)["access_token"]


@pytest.fixture(scope="session")
def player_token():
    return _login(PLAYER)["access_token"]


@pytest.fixture(scope="session")
def coach_token():
    return _login(COACH)["access_token"]


def H(token):
    return {"Authorization": f"Bearer {token}"}


def _no_mongo_id(obj):
    if isinstance(obj, dict):
        assert "_id" not in obj, f"_id leaked in {list(obj.keys())[:5]}"
        for v in obj.values():
            _no_mongo_id(v)
    elif isinstance(obj, list):
        for v in obj:
            _no_mongo_id(v)


# ────────── Health ──────────
def test_health():
    r = requests.get(f"{API}/health", timeout=10)
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ────────── Auth / RBAC on register ──────────
class TestAuth:
    def test_admin_login(self):
        d = _login(ADMIN)
        assert d["user"]["role"] == "admin"
        assert d["user"]["email"] == ADMIN["email"]
        _no_mongo_id(d["user"])

    def test_player_login(self):
        d = _login(PLAYER)
        assert d["user"]["role"] == "player"
        _no_mongo_id(d["user"])

    def test_register_player_succeeds(self):
        email = f"TEST_player_{uuid.uuid4().hex[:8]}@demo.in"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "test123", "name": "Test Player", "role": "player"
        }, timeout=15)
        assert r.status_code == 200, r.text
        u = r.json()["user"]
        assert u["role"] == "player" and u["email"] == email.lower()
        # FIFA card stats should exist for player
        assert isinstance(u.get("attributes"), dict) and len(u["attributes"]) == 6
        assert isinstance(u.get("overall"), int)

    def test_register_coach_succeeds(self):
        email = f"TEST_coach_{uuid.uuid4().hex[:8]}@demo.in"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "test123", "name": "Test Coach", "role": "coach"
        }, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["user"]["role"] == "coach"

    @pytest.mark.parametrize("role", ["admin", "turf_owner", "referee"])
    def test_register_blocked_roles(self, role):
        r = requests.post(f"{API}/auth/register", json={
            "email": f"TEST_blk_{role}_{uuid.uuid4().hex[:6]}@demo.in",
            "password": "test123", "name": "X", "role": role
        }, timeout=15)
        assert r.status_code == 422, f"role={role} should be 422 got {r.status_code} {r.text}"

    def test_login_bad_password(self):
        r = requests.post(f"{API}/auth/login",
                          json={"email": ADMIN["email"], "password": "wrong"}, timeout=15)
        assert r.status_code == 401

    def test_protected_without_token(self):
        r = requests.get(f"{API}/auth/me", timeout=10)
        assert r.status_code == 401

    def test_admin_endpoint_with_player_token(self, player_token):
        r = requests.get(f"{API}/admin/stats", headers=H(player_token), timeout=10)
        assert r.status_code == 403


# ────────── Admin create-user RBAC ──────────
class TestAdminCreateUser:
    def test_create_turf_owner(self, admin_token):
        email = f"TEST_owner_{uuid.uuid4().hex[:8]}@demo.in"
        r = requests.post(f"{API}/admin/create-user", headers=H(admin_token), json={
            "email": email, "password": "owner123", "name": "T Owner", "role": "turf_owner"
        }, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["user"]["role"] == "turf_owner"

    def test_create_referee(self, admin_token):
        email = f"TEST_ref_{uuid.uuid4().hex[:8]}@demo.in"
        r = requests.post(f"{API}/admin/create-user", headers=H(admin_token), json={
            "email": email, "password": "ref123", "name": "T Ref", "role": "referee"
        }, timeout=15)
        assert r.status_code == 200, r.text
        u = r.json()["user"]
        assert u["role"] == "referee"
        assert u.get("cert_level") == "AIFF Level 2"

    @pytest.mark.parametrize("role", ["player", "coach", "admin"])
    def test_create_user_blocked_roles(self, admin_token, role):
        r = requests.post(f"{API}/admin/create-user", headers=H(admin_token), json={
            "email": f"TEST_blk2_{role}_{uuid.uuid4().hex[:6]}@demo.in",
            "password": "x123", "name": "x", "role": role
        }, timeout=15)
        assert r.status_code == 422, f"role={role} should be 422, got {r.status_code} {r.text}"

    def test_non_admin_cannot_create(self, player_token):
        r = requests.post(f"{API}/admin/create-user", headers=H(player_token), json={
            "email": f"TEST_no_{uuid.uuid4().hex[:6]}@demo.in",
            "password": "x123", "name": "x", "role": "referee"
        }, timeout=15)
        assert r.status_code == 403


# ────────── Admin stats / seed ──────────
class TestAdminStats:
    def test_stats(self, admin_token):
        r = requests.get(f"{API}/admin/stats", headers=H(admin_token), timeout=10)
        assert r.status_code == 200
        s = r.json()
        # Seeds: 5 players, 2 coaches, 4 turfs, 3 matches, 5 posts (plus any TEST_* added)
        assert s["players"] >= 5
        assert s["coaches"] >= 2
        assert s["turfs"] >= 4
        assert s["matches_total"] >= 3
        assert s["posts"] >= 5

    def test_seed_idempotent(self, admin_token):
        # Run twice, counts shouldn't grow
        r1 = requests.get(f"{API}/admin/stats", headers=H(admin_token), timeout=10).json()
        requests.post(f"{API}/admin/seed", timeout=30)
        requests.post(f"{API}/admin/seed", timeout=30)
        r2 = requests.get(f"{API}/admin/stats", headers=H(admin_token), timeout=10).json()
        assert r1["players"] == r2["players"]
        assert r1["coaches"] == r2["coaches"]
        assert r1["turfs"] == r2["turfs"]
        assert r1["posts"] == r2["posts"]


# ────────── Posts / Reactions ──────────
class TestPosts:
    def test_list_posts_no_objectid(self):
        r = requests.get(f"{API}/posts", timeout=10)
        assert r.status_code == 200
        posts = r.json()
        assert isinstance(posts, list) and len(posts) >= 5
        _no_mongo_id(posts)
        # Schema check
        p = posts[0]
        assert {"id", "user_id", "user_name", "content", "reactions", "created_at"}.issubset(p.keys())

    def test_create_and_react(self, player_token):
        # Create post
        r = requests.post(f"{API}/posts", headers=H(player_token),
                          json={"content": "TEST_post content"}, timeout=15)
        assert r.status_code == 200, r.text
        pid = r.json()["id"]

        # React fire
        r = requests.post(f"{API}/posts/{pid}/react", headers=H(player_token),
                          json={"reaction": "fire"}, timeout=10)
        assert r.status_code == 200
        body = r.json()
        assert body["reactions"]["fire"] == 1
        assert body["my_reaction"] == "fire"

        # Switch to boot
        r = requests.post(f"{API}/posts/{pid}/react", headers=H(player_token),
                          json={"reaction": "boot"}, timeout=10).json()
        assert r["reactions"]["fire"] == 0
        assert r["reactions"]["boot"] == 1
        assert r["my_reaction"] == "boot"

        # Toggle off (same reaction)
        r = requests.post(f"{API}/posts/{pid}/react", headers=H(player_token),
                          json={"reaction": "boot"}, timeout=10).json()
        assert r["reactions"]["boot"] == 0
        assert r["my_reaction"] is None


# ────────── Matches: full pipeline ──────────
class TestMatchPipeline:
    @pytest.fixture(scope="class")
    def turf_id(self):
        r = requests.get(f"{API}/turfs", timeout=10)
        assert r.status_code == 200 and len(r.json()) > 0
        return r.json()[0]["id"]

    @pytest.fixture(scope="class")
    def match_id(self, admin_token, turf_id):
        r = requests.post(f"{API}/matches", headers=H(admin_token), json={
            "home_team": "TEST_FC_A", "away_team": "TEST_FC_B",
            "turf_id": turf_id,
            "scheduled_at": "2026-06-01T10:00:00+00:00",
            "format": "5v5",
        }, timeout=15)
        assert r.status_code == 200, r.text
        m = r.json()
        assert m["status"] == "scheduled"
        assert m["camera_status"] == "idle"
        assert m["broadcast_active"] is False
        return m["id"]

    def test_start_match(self, admin_token, match_id):
        r = requests.post(f"{API}/matches/{match_id}/start",
                          headers=H(admin_token), timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["camera_status"] == "recording"
        assert r.json()["broadcast_active"] is True

        # Verify GET match shows live
        m = requests.get(f"{API}/matches/{match_id}", timeout=10).json()
        assert m["status"] == "live"
        assert m["broadcast_active"] is True
        # camera_on event emitted
        assert any(e["type"] == "camera_on" for e in m["events"])

    def test_goal_increments_score(self, admin_token, match_id):
        # Goal for home
        r = requests.post(f"{API}/matches/{match_id}/events", headers=H(admin_token),
                          json={"type": "goal", "team": "TEST_FC_A",
                                "player_name": "Striker A", "minute": 12}, timeout=10)
        assert r.status_code == 200
        ev = r.json()
        assert ev["type"] == "goal" and ev["auto_detected"] is False

        m = requests.get(f"{API}/matches/{match_id}", timeout=10).json()
        assert m["score"]["home"] == 1
        assert m["score"]["away"] == 0

        # Goal for away
        requests.post(f"{API}/matches/{match_id}/events", headers=H(admin_token),
                      json={"type": "goal", "team": "TEST_FC_B", "minute": 30}, timeout=10)
        m = requests.get(f"{API}/matches/{match_id}", timeout=10).json()
        assert m["score"]["away"] == 1

    def test_manual_foul_event(self, admin_token, match_id):
        r = requests.post(f"{API}/matches/{match_id}/events", headers=H(admin_token),
                          json={"type": "foul", "team": "TEST_FC_A",
                                "player_name": "Defender X", "minute": 22,
                                "notes": "Late tackle"}, timeout=10)
        assert r.status_code == 200
        ev = r.json()
        assert ev["type"] == "foul"
        assert ev["auto_detected"] is False  # Manual physical foul

    def test_offside_check(self, admin_token, match_id):
        # Run multiple times — assert range, not exact outcome
        seen_types = set()
        for _ in range(5):
            r = requests.post(f"{API}/matches/{match_id}/offside-check",
                              headers=H(admin_token), timeout=10)
            assert r.status_code == 200, r.text
            ev = r.json()
            assert ev["type"] in ("offside", "onside")
            assert ev["auto_detected"] is True
            assert 0.82 <= ev["confidence"] <= 0.99
            seen_types.add(ev["type"])
        # Not asserting both outcomes since random — at least one type returned
        assert len(seen_types) >= 1

    def test_broadcast_feed(self, match_id):
        r = requests.get(f"{API}/matches/{match_id}/broadcast", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "match" in data and "events" in data
        events = data["events"]
        assert len(events) > 0
        # newest-first ordering
        for i in range(len(events) - 1):
            assert events[i]["created_at"] >= events[i + 1]["created_at"]
        _no_mongo_id(data)

    def test_complete_match(self, admin_token, match_id):
        r = requests.post(f"{API}/matches/{match_id}/complete",
                          headers=H(admin_token), timeout=15)
        assert r.status_code == 200
        assert r.json()["status"] == "complete"

        m = requests.get(f"{API}/matches/{match_id}", timeout=10).json()
        assert m["status"] == "complete"
        assert m["broadcast_active"] is False
        assert m["camera_status"] == "stopped"
        # camera_off event emitted
        assert any(e["type"] == "camera_off" for e in m["events"])

    def test_analysis(self, match_id):
        r = requests.get(f"{API}/matches/{match_id}/analysis", timeout=10)
        assert r.status_code == 200
        data = r.json()
        for k in ("match", "events", "stats", "summary", "motm", "heatmap_points"):
            assert k in data, f"missing {k}"
        assert isinstance(data["heatmap_points"], list) and len(data["heatmap_points"]) > 0
        assert "name" in data["motm"] and "rating" in data["motm"]
        assert isinstance(data["summary"], str) and len(data["summary"]) > 20
        # stats structure
        for k in ("possession", "shots", "passes", "fouls", "offsides"):
            assert k in data["stats"]
        _no_mongo_id(data)

    def test_non_admin_cannot_start(self, player_token, admin_token, turf_id):
        # Create a fresh scheduled match
        r = requests.post(f"{API}/matches", headers=H(admin_token), json={
            "home_team": "TEST_NoStart_A", "away_team": "TEST_NoStart_B",
            "turf_id": turf_id, "scheduled_at": "2026-06-02T10:00:00+00:00",
        }, timeout=15)
        mid = r.json()["id"]
        r2 = requests.post(f"{API}/matches/{mid}/start",
                           headers=H(player_token), timeout=10)
        assert r2.status_code == 403


# ────────── Explore endpoints ──────────
class TestExplore:
    @pytest.mark.parametrize("path", [
        "coaches", "leaderboard", "teams", "partners",
        "drills", "events", "trophies", "tournaments", "turfs",
    ])
    def test_explore_endpoint(self, path):
        r = requests.get(f"{API}/explore/{path}", timeout=10)
        assert r.status_code == 200, f"{path} -> {r.status_code} {r.text}"
        data = r.json()
        assert isinstance(data, list)
        _no_mongo_id(data)
