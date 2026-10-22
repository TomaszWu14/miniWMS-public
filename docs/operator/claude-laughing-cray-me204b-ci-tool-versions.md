# ci: wersje ruff i mypy z requirements-dev.txt — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-ci-tool-versions` |
| PR | jeszcze nie utworzony |
| Data | 2026-10-21 |
| Ryzyko | niskie — zmienia tylko sposób instalacji narzędzi w CI, aplikacja bez zmian |

## 1. Co zmieniono
- Zmiany widoczne dla użytkowników: nie dotyczy.
- `ci.yml` nie ma już własnych, wpisanych na sztywno wersji `ruff`, `mypy` i `django-stubs` —
  bierze je z `requirements-dev.txt`. Dependabot podbija wersje tylko tam (i w
  `pyproject.toml`), więc wcześniej po jego PR-ze lokalnie działałby np. `ruff` 0.17,
  a w CI dalej 0.15 — różnice formatowania kończyłyby się czerwonym CI.

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | nie dotyczy | PR → zakładka Checks → `CI / lint` → krok „Install dev tooling” | przeczytać log | instaluje `ruff==` w wersji z `requirements-dev.txt` |
| 2 | nie dotyczy | PR → `CI / test` → krok „Type check” | przeczytać log | instaluje `mypy` i `django-stubs` w wersjach z `requirements-dev.txt`, mypy zielony |

## 3. Checklista wdrożenia

### Migracje — na KAŻDEJ bazie
| Baza | Polecenie | Wykonano (kto, kiedy) |
|---|---|---|
| dev (lokalny SQLite) | `python manage.py migrate` | ☐ nie dotyczy — brak migracji |
| test (baza testów) | tworzona automatycznie przez `pytest` / `manage.py test` | ☐ testy zielone |
| demo (jeśli wdrożone) | automatycznie w `entrypoint.sh` przy deployu | ☐ nie dotyczy — brak migracji |
| prod (PostgreSQL, Coolify) | automatycznie w `entrypoint.sh` przy deployu | ☐ nie dotyczy — brak migracji |

Nowe migracje w tym branchu: brak. Odwracalne: nie dotyczy.
Sprawdzenie: `python manage.py showmigrations warehouse` — wszystkie `[X]`.

### Zmienne środowiskowe
| Zmienna | Nowa / zmieniona / usunięta | Wartość prod | Ustawiona w Coolify |
|---|---|---|---|
| — | nie dotyczy | — | ☐ nie dotyczy |

Zaktualizowano też: `.env.example` — nie dotyczy, `.env.docker.example` — nie dotyczy,
`COOLIFY.md` — nie dotyczy.

### Przed i po deployu
- ☐ CI zielone na PR (`ci.yml`, `security.yml`)
- ☐ backup bazy prod sprzed deployu — nie dotyczy (brak migracji)
- ☐ po deployu: nie dotyczy (zmiana tylko w CI)

## 4. Plan wycofania
1. Kod: revert PR na `main` (Coolify nie używa `ci.yml`).
2. Migracje: nie dotyczy.
3. Zmienne środowiskowe: nie dotyczy.
4. Weryfikacja po wycofaniu: CI na `main` zielone.
