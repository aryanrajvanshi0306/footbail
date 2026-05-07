# footbAIl.in — Product Requirements Document (Living)

> Last updated: 2026-05-07 · **Iteration 2** (Design refresh + GPT-4o-mini wired + Share Reel + City Anime Theming)

## 1. Vision

India's first AI-powered Football Operating System. A "player intelligence platform" — booking is just the entry point; the moat is data + AI-driven performance improvement (FIFA-style player cards, AI video analysis, VAR-grade match control).

## Iteration 2 — What Changed (2026-05-07)

After the user pasted their senior-engineer build protocol + design system + city anime theming spec, four high-impact deliverables shipped while keeping the Emergent-platform-compatible MongoDB+JWT+CRA stack:

1. **Design system refresh** — new tokens applied: bg `#0A0F1E`/`#1C2333`/`#243046`, accents `green #00E676` (CTA/LIVE) · `blue #38BDF8` (links/coach) · `amber #FFB830` (XP/warnings) · `red #FF4D4D` (danger/red cards) · `purple #A78BFA` (AI/OYP) · `gold #F59E0B` (MOTM). DM Sans + JetBrains Mono. 12px radius globally. Back-compat aliases keep all existing JSX functioning.

2. **City Anime Theming System** — `/app/frontend/src/lib/cityTheme.js` exposes 8 cities × `{accent, subtitle, pushPrefix, pattern}`. Applied via CSS var `--city-accent` + `--city-pattern` (SVG data-URI) on `:root` from `AppShell` based on logged-in user's city. **Never names anime; never uses character names.** Subtitles like "Straw Hat City", "Hidden Leaf", "Plus Ultra", "Cursed City", "Power Spark", "The Wall", "Breath of Flame", "Gotta Catch" speak in coded language only.
   - Mumbai → `#F5A623` gold · ocean wave SVG
   - Delhi → `#FF6B00` orange · kunai/star SVG
   - Bangalore → `#00C853` emerald · circuit node SVG
   - Kolkata → `#7C3AED` violet · cursed eye/spiral SVG
   - Chennai → `#FFD600` yellow · power spark SVG
   - Hyderabad → `#00897B` teal · stone wall SVG
   - Pune → `#E91E63` red · wisteria petal SVG
   - Kochi → `#FFEB3B` electric · pokéball arc SVG

3. **Real GPT-4o-mini match analysis** — `_ai_match_summary()` in `server.py` calls `emergentintegrations.llm.chat.LlmChat.with_model("openai", "gpt-4o-mini")` using the Emergent LLM key. 20s timeout, async, graceful fallback to template if API fails. Results cached in new `match_analysis` collection (per-match) so subsequent calls are instant. Verified end-to-end: returns crisp 3-paragraph tactical analysis (~1,170 chars). Response includes `summary_source` field (`gpt-4o-mini` or `cache` or `fallback`).

4. **Share Highlight Reel (viral loop)** — `/app/frontend/src/components/ShareHighlight.jsx`. Renders a 9:16 vertical share card live-previewed on Match Analysis page using the user's city accent + city subtitle (e.g. "STRAW HAT CITY" for Mumbai). On tap: `html2canvas` exports PNG → Web Share API on mobile (IG/WhatsApp), download fallback on desktop. Card shows huge MOTM rating, name, position, GOALS/ASSISTS/TEAM pills, match strip, and "made with footbAIl" wordmark.

## 2. Original Problem Statement (verbatim)

(unchanged — see iteration 1 section below)

## 3. Architecture (MVP)

| Layer | Tech |
|---|---|
| Frontend | React 18 (CRA) + Tailwind 3 + lucide-react + sonner + html2canvas |
| Backend | FastAPI 0.115 + Motor + JWT (HS256) + bcrypt + emergentintegrations (GPT-4o-mini) |
| Storage | MongoDB (collections: users, turfs, posts, matches, match_events, match_analysis) |
| Hosting | Supervisor: backend on `0.0.0.0:8001`, frontend on `0.0.0.0:3000` |
| AI | OpenAI GPT-4o-mini via Emergent LLM key (3-paragraph match analysis, cached per match) |

PRD's PostgreSQL/Celery/SageMaker/Razorpay/OTP intentionally deferred to real-infra phase since they don't run on this Emergent supervisor environment. All backend collections + frontend routes are **MongoDB-and-JWT-equivalent of the spec** with identical UX semantics.

## 4. User Roles

(unchanged)

## 5. Implemented (Iter 1 — 2026-05-06)

(see iteration 1 below)

## 6. Implemented (Iter 2 — 2026-05-07)

### Frontend
- ✅ `/app/frontend/tailwind.config.js` — full token refresh + back-compat
- ✅ `/app/frontend/src/index.css` — `:root` CSS vars for `--city-accent`, `--city-pattern` + utility classes (`.city-shine`, `.city-pattern`, `.city-ring`, `.lfg-glow`, animated camera scan)
- ✅ `/app/frontend/src/lib/cityTheme.js` — 8-city theme map + `applyCityTheme(city)` mounter
- ✅ `/app/frontend/src/components/AppShell.jsx` — applies city theme on mount; topbar shows user's city in their accent color; top tile uses city accent
- ✅ `/app/frontend/src/components/ShareHighlight.jsx` — 9:16 viral share card, html2canvas → Web Share / PNG download
- ✅ Login: green KICK OFF on black text (proper contrast), wordmark `foot[bAI]l` with green AI accent

### Backend
- ✅ `EMERGENT_LLM_KEY` added to `/app/backend/.env`
- ✅ `_ai_match_summary()` async function — GPT-4o-mini via emergentintegrations w/ 20s timeout + fallback
- ✅ `match_analysis` collection — per-match cache (idempotent on re-fetch)
- ✅ `GET /api/matches/{id}/analysis` now returns `summary_source: "gpt-4o-mini" | "cache" | "fallback"`

### Verified end-to-end
- ✅ GPT-4o-mini returns 3-paragraph (~1,170 char) tactical analysis in ~5.7s on first call, then cached (instant)
- ✅ City theme rendered correctly: Mumbai user sees gold accent, "STRAW HAT CITY" subtitle, ocean wave pattern
- ✅ Share Reel preview renders inline at 270×480 with all stats; PNG export tested via html2canvas
- ✅ All RBAC paths still pass (38/38 from iter 1 still green; player→event still 403)

## 7. Backlog (Prioritized)

**P0 (next iter):**
1. Apply city accent rings to FIFA card on Profile (`.city-ring`)
2. Coach signup flow → `coach` role lands on dedicated coach landing
3. Wire Gemini Nano Banana for player avatar generation
4. WebSocket live broadcast (replace 3s polling)

**P1:**
5. Razorpay test-mode booking flow
6. Phone OTP via Firebase
7. PWA manifest + offline ticket cache
8. Persistent AI Coach chat (history per player)

**P2:**
9. Real video upload (S3 + HLS)
10. Hindi i18n
11. AIFF compliance PDF report
12. Squad availability polls + recurring fixtures

## 8. Test Credentials
See `/app/memory/test_credentials.md`

---

## ARCHIVE — Iteration 1 (2026-05-06)

### Frontend (10 routes + 5-tab shell)
- ✅ `/login` — dark hero w/ stadium bg, quick-login chips for Player/Coach/Admin
- ✅ `/register` — 3-step (Role → Details → Password), role limited to player|coach
- ✅ Bottom nav: **Home · Matches · Feed · Explore · Profile** (Coach tab renamed to **Explore**)
- ✅ `/home` — Greeting, FIFA card preview, post composer, social feed w/ 5 reactions, FAB → Create Match
- ✅ `/matches` + `/matches/create` — 5-step booking
- ✅ `/matches/:id` — Facts/Lineup/Stats/H2H tabs
- ✅ `/feed` — Same posts surface, filter chips
- ✅ `/explore` — **3×3 grid**: Coach, Teams, Partners, Leaderboard, Drills, Events, Turfs, Trophies, Tournaments
- ✅ `/profile` — Large FIFA card, XP bar, stats grid, last-10 form chart
- ✅ `/admin` — Control Room dashboard (no Reports)
- ✅ `/admin/users` — Filterable table + create turf_owner / referee modal
- ✅ `/admin/turfs` — Add turf modal w/ owner dropdown
- ✅ `/admin/match-control` — Schedule + matches list, opens VAR Room
- ✅ `/admin/var/:id` — **VAR Room** (idle → Start Camera → live broadcast w/ event controls + AI offside)
- ✅ `/broadcast/:id` — Spectator polling viewer
- ✅ `/match/:id/analysis` — Performance Analysis

### Backend (24 endpoints)
- Auth · Admin · Turfs · Posts (with reactions) · Matches (full pipeline) · 9 Explore endpoints
- All `/api`-prefixed; RBAC enforced; no `_id` leaks
- Match pipeline verified: schedule → camera-on → events → AI offside → camera-off → analysis

### Test Coverage
- 38/38 backend tests passed (testing agent iteration 1)

## 9. Smart Enhancement (revenue lever) — DELIVERED in Iter 2 ✅
"Share Highlight Reel for Instagram" auto-renders 9:16 vertical PNG with user's MOTM stats on city-themed background. Drives organic discovery via every player's IG story. Implemented in `ShareHighlight.jsx`.

## 1. Vision

India's first AI-powered Football Operating System. A "player intelligence platform" — booking is just the entry point; the moat is data + AI-driven performance improvement (FIFA-style player cards, AI video analysis, VAR-grade match control).

## 2. Original Problem Statement (verbatim)

> read the prd completely and ask every open ended questions and assumption before building anything 
> plan like a team product design devlopment in sync
> Home tab - social feed - text message
> Coach plus more option 3x 3 grid menu option
> Coach tab change to explore name
> On- boarding mei sirf players and coaches
> Admin have the authority turf owner and refree manually
> Remove reports option
> In match control click to schedule the match the camera will start of the turf
> Offside camera se detect
> Physical foul will input the data in the app
> Offside detection and rechecking
> Var monitor type control kickoff foul complete
> Live share at of any fouls goal yellow Live broadcast of match
> Match performance analysis
> Match complete the camera will stop the match recording

User shipped: footbAIl_PRD_Supreme_v3.docx + 4 reference screenshots (structure, matches, home).

## 3. Architecture (MVP)

| Layer | Tech |
|---|---|
| Frontend | React 18 (CRA) + Tailwind + lucide-react + sonner toasts + react-router |
| Backend | FastAPI 0.115 (single file `server.py`) + Motor (async MongoDB) + JWT (HS256) + bcrypt |
| Storage | MongoDB (collections: users, turfs, posts, matches, match_events) |
| Hosting | Supervisor: backend on `0.0.0.0:8001`, frontend on `0.0.0.0:3000` |

Original PRD called for PostgreSQL + Celery + S3 + SageMaker — replaced with MongoDB + mocked AI/camera for MVP since this is a clickable end-to-end prototype on the Emergent platform.

## 4. User Roles

| Role | Self-signup? | Created By | Can do |
|---|---|---|---|
| `player` | ✅ | self | Browse feed, post, react, book matches, view FIFA card |
| `coach` | ✅ | self | Same as player + (future) coach marketplace |
| `admin` | ❌ | seed | Full Control Room, schedule matches, run VAR |
| `turf_owner` | ❌ | admin | (future) Manage own turfs |
| `referee` | ❌ | admin | Run VAR room, fire match events |

## 5. Implemented (Iter 1 — 2026-05-06)

### Frontend (10 routes + 5-tab shell)
- ✅ `/login` — dark hero w/ stadium bg, quick-login chips for Player/Coach/Admin
- ✅ `/register` — 3-step (Role → Details → Password), role limited to player|coach
- ✅ Bottom nav: **Home · Matches · Feed · Explore · Profile** (Coach tab renamed to **Explore**)
- ✅ `/home` — Greeting, FIFA card preview, post composer, social feed w/ 5 reactions (boot, gloves, whistle, fire, 100), FAB → Create Match
- ✅ `/matches` + `/matches/create` — 5-step booking (team → opponent → turf+slot → mock pay → confirm)
- ✅ `/matches/:id` — Facts/Lineup/Stats/H2H tabs
- ✅ `/feed` — Same posts surface, filter chips
- ✅ `/explore` — **3×3 grid**: Coach, Teams, Partners, Leaderboard, Drills, Events, Turfs, Trophies, Tournaments
- ✅ `/explore/:section` — Each section detail page
- ✅ `/profile` — Large FIFA card (tier-tinted gradient), XP bar, stats grid, last-10 form chart
- ✅ `/admin` — Control Room dashboard w/ 8-stat grid + 3 action cards (no Reports)
- ✅ `/admin/users` — Filterable table + modal to create turf_owner / referee
- ✅ `/admin/turfs` — Add turf modal w/ owner dropdown
- ✅ `/admin/match-control` — Schedule match modal + matches list, opens VAR Room
- ✅ `/admin/var/:id` — **VAR Room**: idle camera state → Start Camera (1.5s scanning anim) → live SVG-pitch broadcast w/ animated player dots + ball, match clock; controls: Kickoff, Goal, Foul (physical), Yellow, Red, Offside (AI w/ confidence%), Sub, Complete; live offside review pane (Confirm/Overturn); event log (newest-first)
- ✅ `/broadcast/:id` — Spectator view, polls every 3s, lower-third event banner
- ✅ `/match/:id/analysis` — Performance Analysis: stats bars, MOTM card, AI summary, heatmap

### Backend (24 endpoints, all `/api`-prefixed)
- ✅ `POST /api/admin/seed` (idempotent: 1 admin, 5 players, 2 coaches, 4 turfs, 5 posts, 3 matches)
- ✅ Auth: `register` (role∈{player,coach}), `login`, `me`
- ✅ Admin: `create-user` (role∈{turf_owner,referee}), `users` (list/filter), `stats`
- ✅ Turfs: list, create
- ✅ Posts: list, create, react (toggle)
- ✅ Matches: list, get, create, **start camera**, **add event**, **offside-check (AI sim)**, **complete (stop camera)**, broadcast feed, analysis
- ✅ Explore: 9 endpoints (coaches, leaderboard, teams, partners, drills, events, trophies, tournaments, turfs)
- ✅ RBAC enforced on `/admin/*`, match `/start`, `/complete`, `/events`, `/offside-check`
- ✅ All responses scrub `_id` and `password_hash`

### Match Control Pipeline (verified end-to-end)
```
Schedule match (admin)
  → Open VAR Room
  → Start Camera (POST /start) → status=live, broadcast_active=true, camera_status=recording, emits camera_on event
  → Fire events (POST /events): kickoff/goal(scores!)/foul/yellow/red/sub
  → AI Offside Check (POST /offside-check) → random offside|onside, confidence∈[0.82,0.99], auto_detected=true
  → Match Complete (POST /complete) → status=complete, broadcast_active=false, camera_status=stopped, emits camera_off event
  → View Performance Analysis (GET /analysis) → stats, summary, MOTM, heatmap
```

### Test Coverage
- ✅ **38/38 backend tests passed** (testing agent, iteration 1)
- ✅ All RBAC paths verified (401 without token, 403 for wrong role)
- ✅ No `_id` leaks in any response

## 6. NOT Implemented (deliberately deferred for clickable MVP)

| Area | Status | Why |
|---|---|---|
| Real Razorpay payments | UI-mocked "Pay Now (Mock)" button | No keys; deferred per user choice |
| Real camera / WebRTC / S3 video upload | SVG pitch + animated dots | No GPU/AI infra in this env |
| Real YOLOv9 offside detection | Random sim w/ realistic confidence | Same |
| Phone OTP (Firebase/MSG91) | JWT email+password | No Firebase keys; faster iter |
| OpenAI GPT-4o match analysis | Template string | Can be wired with Emergent LLM key in iter 2 |
| WhatsApp invitations | — | Defer to integration phase |
| Video annotation tools (7-tool canvas) | — | Out of MVP scope |
| Coach Marketplace booking + payouts | Browse only | Defer |
| PWA + offline (Workbox + IndexedDB) | — | Defer |
| Recurring fixtures, squad polling | — | Defer |
| AIFF compliance PDF (WeasyPrint) | — | Defer |

## 7. Backlog (Prioritized)

**P0 (next iter, if user requests):**
1. Wire OpenAI GPT-4o for real AI match analysis text using Emergent LLM key
2. Wire Gemini Nano Banana for player avatar generation per user
3. Add referee VAR-room access (currently admin-only practical UX)
4. Player Card upgrade animation on tier change (confetti modal)

**P1:**
5. Razorpay test-mode booking flow
6. Coach session booking + drill assignments
7. Phone OTP via Firebase
8. Persistent AI Coach chat (LangChain + match-history context)

**P2:**
9. Real video upload (S3 + HLS)
10. PWA + offline ticket cache
11. Hindi i18n
12. Squad availability polls + recurring fixtures

## 8. Test Credentials
See `/app/memory/test_credentials.md`

## 9. Smart Enhancement (revenue lever)
Add a one-tap "**Highlight Reel for Instagram**" share on the Match Performance Analysis page — auto-generates a 9:16 vertical card with the user's MOTM stat overlaid on a goal moment. Acts as organic distribution and drives sign-ups from non-users who watch the clip on social. Cost: ~80 lines of HTML2Canvas + a styled card component. ROI: every shared reel = ~3-5 free new signups based on FIFA Mobile/Strava patterns.
