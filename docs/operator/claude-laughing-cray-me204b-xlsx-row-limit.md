# claude/laughing-cray-me204b-xlsx-row-limit — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-xlsx-row-limit` |
| PR | jeszcze nie utworzony |
| Data | 2026-10-24 |
| Ryzyko | niskie — dodatkowy limit wierszy w importach; zwykłe pliki (do 10 000 wierszy) działają jak dotąd |

## 1. Co zmieniono
- Importy CSV/XLSX (lokalizacje, stany, przyjęcia, wydania) odrzucają pliki z więcej niż 10 000 wierszy
  komunikatem „Błąd importu: Plik ma za dużo wierszy — import obejmuje najwyżej 10000 wierszy.”
  Nic nie jest zapisywane.
- Technicznie: ochrona przed „zip bombą” (mały .xlsx rozpakowujący się do milionów wierszy). Plik jest
  czytany strumieniowo i przerywany po przekroczeniu limitu. Limit to `MAX_IMPORT_ROWS` w
  `config/settings/base.py`; w trybie demo nadal obowiązuje `DEMO_IMPORT_MAX_ROWS` (500).
- Doprecyzowano pułapkę nr 6 w `docs/pitfalls/views.md`.

## 2. Kroki do ręcznego sprawdzenia
| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | Administrator | import lokalizacji | wgraj plik .xlsx z kilkoma wierszami | import kończy się sukcesem |
| 2 | Administrator | import lokalizacji | wgraj plik z >10 000 wierszy | komunikat o zbyt dużej liczbie wierszy, brak zmian w bazie |

## 3. Checklista wdrożenia

### Migracje — na KAŻDEJ bazie
| Baza | Polecenie | Wykonano (kto, kiedy) |
|---|---|---|
| dev (lokalny SQLite) | nie dotyczy | nie dotyczy |
| test (baza testów) | tworzona automatycznie przez `pytest` | ☐ testy zielone (273 passed, 2 skipped) |
| demo (jeśli wdrożone) | nie dotyczy | nie dotyczy |
| prod (PostgreSQL, Coolify) | nie dotyczy | nie dotyczy |

Nowe migracje w tym branchu: brak. Odwracalne: nie dotyczy.
Sprawdzenie: `python manage.py showmigrations warehouse` — bez zmian.

### Zmienne środowiskowe
| Zmienna | Nowa / zmieniona / usunięta | Wartość prod | Ustawiona w Coolify |
|---|---|---|---|
| — (stała `MAX_IMPORT_ROWS` w kodzie, nie env) | nie dotyczy | nie dotyczy | nie dotyczy |

### Przed i po deployu
- ☐ CI zielone na PR (`ci.yml`, `security.yml`)
- backup bazy: nie dotyczy (brak migracji)
- ☐ po deployu: `/healthz` zwraca `{"status": "ok"}`
- ☐ kroki z sekcji 2 wykonane na prod

## 4. Plan wycofania
1. Kod: Coolify → zasób → **Deployments** → poprzedni deployment → **Redeploy** (albo revert PR na `main`).
2. Migracje: nie dotyczy.
3. Zmienne środowiskowe: nie dotyczy.
4. Weryfikacja po wycofaniu: `/healthz`, logowanie, import lokalizacji.
