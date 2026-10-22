# claude/laughing-cray-me204b-dependabot — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-dependabot` |
| PR | utworzony razem z tym plikiem (draft) |
| Data | 2026-10-22 |
| Ryzyko | niskie — tylko konfiguracja Dependabota; kod aplikacji i deploy bez zmian |

## 1. Co zmieniono

- `.github/dependabot.yml`:
  - **docker** dostaje grupę `docker` dla aktualizacji minor/patch (pip i github-actions miały
    już grupy) — mniej osobnych PR-ów,
  - **pip**: ignorowane aktualizacje `version-update:semver-major` dla `django` — repo zostaje
    na Django 5.2 LTS (`Django>=5.2,<5.3`); poprawki 5.2.x nadal przychodzą w grupie `pip`.
- Harmonogramy bez zmian (weekly dla wszystkich ekosystemów).

Zmiany widoczne dla użytkowników magazynu: brak.

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | właściciel repo | GitHub → Insights → Dependency graph → Dependabot | po scaleniu: sprawdzić ostatnie sprawdzenie `dependabot.yml` | brak błędów konfiguracji |
| 2 | właściciel repo | GitHub → Pull requests | po najbliższym cotygodniowym przebiegu | brak PR-a z Django 6.x; aktualizacje obrazu minor/patch w jednym PR-ze grupy `docker` |

Istniejące PR-y Dependabota (np. #25 z obrazem Pythona) nie są tu ruszane.

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

Sprawdzenie lokalne: YAML poprawny (`yaml.safe_load`), struktura zgodna ze schematem v2.

## 4. Plan wycofania
1. Kod: revert PR na `main`.
2. Migracje: nie dotyczy.
3. Zmienne środowiskowe: nie dotyczy.
4. Weryfikacja po wycofaniu: Dependabot znów tworzy osobne PR-y dla obrazu Dockera.
