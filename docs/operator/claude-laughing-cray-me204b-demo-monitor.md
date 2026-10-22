# claude/laughing-cray-me204b-demo-monitor — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-demo-monitor` |
| PR | utworzony razem z tym plikiem (draft) |
| Data | 2026-10-22 |
| Ryzyko | niskie — nowy workflow GitHub Actions; kod aplikacji i deploy bez zmian |

## 1. Co zmieniono

- Nowy workflow `.github/workflows/demo-monitor.yml` („Monitor demo”): co 6 godzin (minuta 17)
  i ręcznie (*Run workflow*) sprawdza publiczne demo `https://miniwms.twapp.pl`:
  - `/healthz` zwraca `{"status": "ok"}` (aplikacja + baza),
  - strona główna `/` odpowiada 200 (po przekierowaniu na logowanie),
  - `/login/` zawiera przycisk „Wejdź jako demo”.
  curl: timeout 30 s, 3 ponowienia co 20 s.
- Awaria → issue „Demo nie odpowiada” z etykietą `demo` (etykieta tworzona automatycznie);
  kolejne awarie dopisują komentarz do otwartego issue, przebieg jest czerwony (mail z GitHub).
  Pierwszy udany przebieg zamyka issue komentarzem „Demo znów działa”.
- Uprawnienia: tylko `issues: write`, tylko `GITHUB_TOKEN` (żadnych sekretów).

Zmiany widoczne dla użytkowników magazynu: brak.

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | właściciel repo | GitHub → Actions → „Monitor demo” | po scaleniu: *Run workflow* na `main` | zielony przebieg, w podsumowaniu „Demo działa” |
| 2 | właściciel repo | GitHub → Issues | sprawdzić po przebiegu | brak issue z etykietą `demo` (gdy demo działa) |

Workflow z `schedule`/`workflow_dispatch` uruchamia się dopiero z gałęzi domyślnej — przed
scaleniem nie da się go odpalić.

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
- ☐ po scaleniu: ręczny przebieg „Monitor demo” zielony
- ☐ kroki z sekcji 2 wykonane

Sprawdzenie lokalne: `actionlint 1.7.7` — bez uwag; YAML poprawny (`yaml.safe_load`).

## 4. Plan wycofania
1. Kod: revert PR na `main` albo GitHub → Actions → „Monitor demo” → *Disable workflow*.
2. Migracje: nie dotyczy.
3. Zmienne środowiskowe: nie dotyczy.
4. Weryfikacja po wycofaniu: workflow nie pojawia się w Actions / jest wyłączony; ewentualne
   otwarte issue z etykietą `demo` zamknąć ręcznie.
