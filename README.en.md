<img src="docs/brand/logo.png" alt="miniWMS" width="360">

# miniWMS

[![ci](https://github.com/TomaszWu14/miniWMS-public/actions/workflows/ci.yml/badge.svg)](https://github.com/TomaszWu14/miniWMS-public/actions/workflows/ci.yml)

🇵🇱 [Polska wersja](README.md) · 🇬🇧 English

**Brings order to material flow in a small warehouse that used to keep its records on paper —
for warehouse operators and their managers.**

![Putting a pallet away with a phone scanner: scan pallet, scan location, confirm](docs/screenshots/demo.gif)

📹 [Walkthrough video — 3 min, Polish captions](docs/video/youtube/miniwms-youtube.mp4)
· [shorter version — 2 min](docs/video/miniwms-demo.mp4)

🌐 **Live demo, no sign-up: <https://miniwms.twapp.pl/demo/>** — opens straight into the app
with a 3-minute guided tour. The login screen also has a **“Wejdź jako demo”** (enter as demo)
button, or log in as `demo_operator` (Operator) or `demo_podglad` (read-only), password
`demo1234`. All data is fictional and resets every night at 3:00, or immediately with the
**“Przywróć dane demo”** (restore demo data) button in the banner. Click around freely.

> The user interface and the analysis documents are in Polish — the app was designed for a
> Polish warehouse team. This page is a full English summary.

### Try it in 5 minutes

The dashboard opens with a “getting started” panel listing the same steps:

1. **Pallets with QR labels** — *HU (palety)* → a pallet marked “Do ułożenia” (to put away) →
   *Etykieta* (label, PDF).
2. **Scanner: put a pallet away** — [/skaner/](https://miniwms.twapp.pl/skaner/) →
   *Rozmieszczanie* (put-away): pallet number, then location code (the phone camera works).
3. **Picking by FEFO** — *Wydania* (issues) → an “Otwarte” (open) document: the system
   suggests the pallets with the earliest expiry date; *Realizuj* (complete) deducts the stock.
4. **Occupancy report** — *Raporty* → *Zajętość lokalizacji* (location occupancy).

| Login | Dashboard with the getting-started panel |
|---|---|
| ![Login screen with the “enter as demo” button](docs/screenshots/login-demo.png) | ![Dashboard with the welcome panel and stock tiles](docs/screenshots/dashboard-welcome.png) |
| **Pallet list** | **Issue document with FEFO suggestion** |
| ![Pallet list with number, material, expiry date and location](docs/screenshots/hu-list.png) | ![Issue document suggesting which pallets to pick from](docs/screenshots/issue-detail.png) |

## Problem → solution

About two hundred pallets, thirty new ones a week and two operators on shifts — with paper
records: pallets without labels, the location of goods kept in one person's memory, no
history, and picking regardless of expiry date. miniWMS gives every pallet a number and a QR
label, records its location when it is scanned with a phone, and when goods are issued it
picks the pallets with the earliest expiry date (FEFO). Every stock change leaves a trace:
who, when, how much, from where and to where.

## Analysis documents (Polish)

| Document | Contents |
|---|---|
| [01 — Problem and scope](docs/01-problem-i-zakres.md) | problem, stakeholders, glossary, what is in and out of scope and why |
| [02 — Process](docs/02-proces.md) | as-is and to-be process (Mermaid), actors, decision points, assumptions |
| [03 — User flow](docs/03-user-flow.md) | screen map of the web panel and the scanner, alternative and dead-end paths |
| [04 — Data model](docs/04-model-danych.md) | ERD, 13 entities, integrity rules and their gaps |
| [05 — Requirements](docs/05-wymagania.md) | 26 requirements with acceptance criteria, linked to code and tests |
| [06 — Decisions](docs/06-decyzje.md) | decision log: context, options, rationale, consequences |
| [07 — Limitations](docs/07-ograniczenia.md) | what the app does not do, known issues, next steps |

## How to run

Requires Python 3.11+.

```bash
git clone https://github.com/TomaszWu14/miniWMS-public.git
cd miniWMS-public
python -m venv .venv
source .venv/bin/activate              # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

export DEMO_MODE=1                     # Windows PowerShell: $env:DEMO_MODE=1
python manage.py migrate
python manage.py seed_demo             # fictional data: 15 materials, ~30 pallets, 3 issues, an open stocktake
python manage.py runserver
```

App: <http://127.0.0.1:8000/> · scanner: <http://127.0.0.1:8000/skaner/>

| Login | Role | Password |
|---|---|---|
| `demo_operator` | Operator — receiving, put-away, issues, scanner | `demo1234` |
| `demo_podglad` | Viewer — read-only | `demo1234` |

Without `DEMO_MODE` the app starts with an empty database — create an admin with
`python manage.py createsuperuser`. Tests: `pip install -r requirements-dev.txt` and
`python -m pytest -q`. Server deployment (Docker, Coolify), environment variables and code
structure: [docs/wdrozenie.md](docs/wdrozenie.md) (Polish).

## Stack and why

| Component | Why |
|---|---|
| **Python + Django** | login, roles, forms and admin out of the box — time goes into warehouse rules, not infrastructure |
| **Transactions and row locks** | a pallet's stock change and its history entry are saved together; two concurrent issues from the same pallet cannot take it below zero |
| **PostgreSQL** (SQLite locally) | rules enforced by the database too: quantity ≥ 0, unique pallet and document numbers |
| **ReportLab + qrcode** | pallet labels and the dispatch note (WZ) as PDF with a QR code, no external services |
| **openpyxl, CSV** | the company has no ERP — data goes in and out through spreadsheet files |
| **In-browser scanner (jsQR)** | a phone instead of a dedicated handheld terminal; same rules as the web panel |
| **Docker Compose + Caddy / Coolify** | one command on the server, automatic HTTPS (required for camera access) |
| **GitHub Actions** | tests (SQLite and PostgreSQL), lint, type checks, migration and production-config checks, Docker smoke test on every change |

## Security

Every PR to `main` passes the gates in [`security.yml`](.github/workflows/security.yml)
(the same scans run monthly on the whole repository):

- **gitleaks** — secrets in commits (exceptions: `.gitleaksignore`),
- **Bandit** and **Semgrep** (`p/owasp-top-ten`) — static analysis,
- **Trivy** and **pip-audit** — vulnerable dependencies and misconfiguration (HIGH/CRITICAL with a fix),
- **Dependabot** — weekly updates for pip, the Docker image and GitHub Actions.

The app sends security headers (including `X-Frame-Options`, `Permissions-Policy`, HSTS behind
HTTPS, `no-store` for JSON). Reporting vulnerabilities: [SECURITY.md](SECURITY.md).

## Scope and limitations

In scope: receiving with labels, put-away, issues with pallet selection by expiry date,
corrections, merging pallets, stocktaking, reports and export.

Deliberately out of scope: ERP integration (the company has none), returns, blocking expired
pallets, multiple warehouses. All documented requirements are met and decisions on known
issues are recorded (D-09…D-13); the tests also pass on PostgreSQL, including a race-condition
test. Status: advanced prototype. Details: [07 — Limitations](docs/07-ograniczenia.md).

## Project context

A personal project based on my own experience working in a warehouse. The app was not
deployed at a company — the process, scale and requirements in the documentation come from
that observation.

Company names are replaced with fictional ones, and demo and test data are synthetic. The code
is shared for review only, all rights reserved — see [LICENSE](LICENSE). The repository also
contains the configuration for working with an AI coding assistant (`.claude/`, `CLAUDE.md`,
`docs/pitfalls/`, `docs/operator/`).
