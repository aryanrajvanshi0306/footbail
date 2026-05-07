# footbAIl Test Credentials

> Seed creates these idempotently. Call `POST /api/admin/seed` once before testing (App.js does it on boot).

## Admin (pre-seeded, NOT self-signup)
- **Email:** `admin@footbail.in`
- **Password:** `admin123`
- **Role:** `admin`
- **Capabilities:** Full Control Room, manually create Turf Owner / Referee, schedule matches, run VAR

## Demo Players (seed — multi-city for City Derby)

### Mumbai 🟠 (Straw Hat)
| Email | Pwd | Position | Tier |
|---|---|---|---|
| `arjun@demo.in` | `demo123` | CM | silver |
| `rohit@demo.in` | `demo123` | ST | silver |
| `vikram@demo.in` | `demo123` | GK | bronze |
| `karan@demo.in` | `demo123` | CB | gold |
| `dev@demo.in` | `demo123` | LW | silver |

### Delhi 🟧 (Hidden Leaf)
| `aryan@delhi.in` | `demo123` | CAM | gold |
| `ishan@delhi.in` | `demo123` | RW | silver |
| `manav@delhi.in` | `demo123` | CDM | gold |

### Bangalore 🟢 (Plus Ultra)
| `aditya@blr.in` | `demo123` | ST | gold |
| `rahul@blr.in` | `demo123` | CM | silver |
| `nikhil@blr.in` | `demo123` | LB | silver |

### Kolkata 🟣 (Cursed City)
| `sourav@kol.in` | `demo123` | ST | gold |
| `debjit@kol.in` | `demo123` | CB | silver |

### Chennai 🟡 (Power Spark)
| `vinay@chn.in` | `demo123` | CM | silver |
| `ajith@chn.in` | `demo123` | RW | silver |

### Hyderabad 🟦 (The Wall)
| `imran@hyd.in` | `demo123` | CB | gold |
| `rohan@hyd.in` | `demo123` | GK | silver |

### Pune 🟥 (Breath of Flame)
| `sahil@pune.in` | `demo123` | ST | silver |

### Kochi 🟨 (Gotta Catch)
| `anand@kochi.in` | `demo123` | LW | silver |

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
