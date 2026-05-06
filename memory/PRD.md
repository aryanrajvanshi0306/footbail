# footbAIl.in — Product Requirements Document (Living)

> Last updated: 2026-05-06 · Iteration 1 (MVP scaffold complete)

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
