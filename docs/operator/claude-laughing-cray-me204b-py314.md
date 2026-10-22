# claude/laughing-cray-me204b-py314 — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-py314` |
| PR | utworzony razem z tym plikiem (draft) |
| Data | 2026-10-22 |
| Ryzyko | niskie — tylko CI; obraz Dockera i produkcja zostają na Pythonie 3.11 |

## 1. Co zmieniono

- `ci.yml`, job `test`: macierz `python-version: ["3.11", "3.14"]`, `fail-fast: false`.
  - przebieg 3.11 nadal nazywa się **`test`** (nazwa wymaganego checka bez zmian),
  - nowy przebieg nazywa się **`test (Python 3.14)`** — te same kroki (system check, mypy,
    `check --deploy`, migracje, `manage.py test`).
- `lint`, `test-postgres`, `docker-build` bez zmian (3.11).

Zmiany widoczne dla użytkowników magazynu: brak.

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | właściciel repo | PR → zakładka *Checks* | poczekać na CI | zielone: `lint`, `test`, `test (Python 3.14)`, `test-postgres`, `docker-build` |
| 2 | właściciel repo | Settings → Branches → reguła `main` | sprawdzić wymagane checki | `test` nadal na liście i spełniony; `test (Python 3.14)` opcjonalnie dodać jako wymagany |

## 3. Checklista wdrożenia

### Migracje — na KAŻDEJ bazie
| Baza | Polecenie | Wykonano (kto, kiedy) |
|---|---|---|
| dev (lokalny SQLite) | nie dotyczy | — |
| test (baza testów) | nie dotyczy | — |
| demo (jeśli wdrożone) | nie dotyczy | — |
| prod (PostgreSQL, Coolify) | nie dotyczy | — |

Nowe migracje w tym branchu: brak.

### Zmienne środowiskowe
| Zmienna | Nowa / zmieniona / usunięta | Wartość prod | Ustawiona w Coolify |
|---|---|---|---|
| — | nie dotyczy | | — |

### Przed i po deployu
- ☐ CI zielone na PR (`ci.yml`, `security.yml`)
- ☐ backup bazy — nie dotyczy (brak migracji)
- ☐ kroki z sekcji 2 wykonane

Sprawdzenie lokalne na Pythonie 3.14.6 (świeży venv, `requirements-dev.txt`):
`ruff check .` — All checks passed; `ruff format --check .` — 97 files already formatted;
`mypy warehouse/services.py config/log.py config/urls.py` — no issues in 3 source files;
`manage.py check`, `check --deploy` — no issues; `makemigrations --check` — No changes detected;
`pytest -q` — 227 passed, 2 skipped (także z `-W error::DeprecationWarning`);
`manage.py test` — OK (skipped=2). `actionlint 1.7.7` na `ci.yml` — bez uwag.

## 4. Plan wycofania
1. Kod: revert PR na `main`.
2. Migracje: nie dotyczy.
3. Zmienne środowiskowe: nie dotyczy.
4. Weryfikacja po wycofaniu: w PR-ach znów tylko check `test` (3.11).
