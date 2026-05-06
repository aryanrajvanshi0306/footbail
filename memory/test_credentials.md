# footbAIl Test Credentials

> Seed creates these idempotently. Call `POST /api/admin/seed` once before testing (App.js does it on boot).

## Admin (pre-seeded, NOT self-signup)
- **Email:** `admin@footbail.in`
- **Password:** `admin123`
- **Role:** `admin`
- **Capabilities:** Full Control Room, manually create Turf Owner / Referee, schedule matches, run VAR

## Demo Players (seed)
| Email | Password | Name | Position | Tier |
|---|---|---|---|---|
| `arjun@demo.in` | `demo123` | Arjun Sharma | CM | silver |
| `rohit@demo.in` | `demo123` | Rohit Mehra | ST | silver |
| `vikram@demo.in` | `demo123` | Vikram Rao | GK | bronze |
| `karan@demo.in` | `demo123` | Karan Singh | CB | gold |
| `dev@demo.in` | `demo123` | Dev Patel | LW | silver |

## Demo Coaches (seed)
- `ravi@coach.in` / `demo123` (Coach Ravi Kumar)
- `suresh@coach.in` / `demo123` (Coach Suresh Nair)

## Onboarding Restriction
- `/api/auth/register` accepts ONLY `role: "player" | "coach"`.
- `turf_owner` and `referee` are created by Admin via `POST /api/admin/create-user`.
- Admin self-signup is BLOCKED.

## Quick login UI shortcuts (Login page)
- `Player` button → fills `arjun@demo.in / demo123`
- `Coach` button → fills `ravi@coach.in / demo123`
- `Admin` button → fills `admin@footbail.in / admin123`
