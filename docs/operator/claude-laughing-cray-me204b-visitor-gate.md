# Bramka odwiedzających demo — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-visitor-gate` |
| PR | jeszcze nie utworzony (draft) |
| Data | 2026-10-23 |
| Ryzyko | niskie — dotyczy tylko wejścia na konta demo (`DEMO_MODE`); zwykłe konta bez zmian; nowa tabela, migracja odwracalna |

## 1. Co zmieniono
- Przed wejściem do demo („Wejdź jako demo”, link `/demo/`, ręczne logowanie na `demo_operator` /
  `demo_podglad`) odwiedzający widzi formularz „Zanim wejdziesz do wersji demonstracyjnej,
  przedstaw się, proszę.”: imię, nazwisko, firma (2–100 znaków, bez znaków sterujących),
  obowiązkowa zgoda/klauzula RODO i ukryte pole-pułapka. Bez poprawnych danych demo się nie otwiera.
- Wpis zapisuje się w nowej tabeli `DemoVisitor` (bez IP i user-agenta), wpisy starsze niż 90 dni
  są kasowane przy każdym zapisie; jest też komenda `manage.py purge_demo_visitors`.
- Po przedstawieniu się: podpisane ciasteczko na 30 dni (HttpOnly, SameSite=Lax, Secure na prod).
  Ciasteczko, nie sesja — sesja wygasa po 30 min bezczynności.
- Lista odwiedzających (najnowsi pierwsi) dla administratora: `/odwiedzajacy/` (przycisk
  „Odwiedzający demo” w Użytkownicy) oraz Django admin (poza trybem demo, gdzie admin jest wyłączony).
- Przełącznik `DEMO_VISITOR_GATE` (domyślnie włączony; działa tylko przy `DEMO_MODE=1`).
- „Przywróć dane demo” (`seed_demo --reset`) nie rusza tabeli odwiedzających.
- Nie blokowane: `/healthz`, `/login/`, statyki, zwykłe konta.

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | brak (świeże okno) | `/login/` → „Wejdź jako demo” | kliknąć | formularz „przedstaw się” z klauzulą RODO |
| 2 | brak | formularz | wysłać pusty / bez zgody | błędy przy polach, brak logowania |
| 3 | brak | formularz | wypełnić poprawnie, zaznaczyć zgodę | wejście na pulpit jako `demo_operator` |
| 4 | brak (to samo okno) | wylogować, „Wejdź jako demo” | kliknąć | wejście bez formularza (ciasteczko 30 dni) |
| 5 | brak (nowe okno) | `/login/` → login `demo_podglad` + hasło | zalogować | przekierowanie do formularza, po nim komunikat i ponowne logowanie |
| 6 | administrator | Użytkownicy → „Odwiedzający demo” | otworzyć | lista, najnowsze na górze |
| 7 | `demo_operator` | `/odwiedzajacy/` | otworzyć | brak dostępu |

## 3. Checklista wdrożenia

### Migracje — na KAŻDEJ bazie
| Baza | Polecenie | Wykonano (kto, kiedy) |
|---|---|---|
| dev (lokalny SQLite) | `python manage.py migrate` | ☐ |
| test (baza testów) | tworzona automatycznie przez `pytest` / `manage.py test` | ☐ testy zielone (241 passed, 2 skipped) |
| demo (jeśli wdrożone) | automatycznie w `entrypoint.sh` przy deployu | ☐ sprawdzono log |
| prod (PostgreSQL, Coolify) | automatycznie w `entrypoint.sh` przy deployu | ☐ sprawdzono log |

Nowe migracje w tym branchu: `warehouse/migrations/0009_demovisitor.py`. Odwracalne: tak (CreateModel).
Sprawdzenie: `python manage.py showmigrations warehouse` — wszystkie `[X]`.

### Zmienne środowiskowe
| Zmienna | Nowa / zmieniona / usunięta | Wartość prod | Ustawiona w Coolify |
|---|---|---|---|
| `DEMO_VISITOR_GATE` | nowa (opcjonalna, domyślnie `1`) | `1` | ☐ nie wymagana |

Zaktualizowano też: `.env.example` ☑, `.env.docker.example` nie dotyczy, `COOLIFY.md` §6 nie dotyczy (zmienna opcjonalna).

Uwaga: RODO — wpisy kasują się przy zapisie nowego wpisu; opcjonalnie dodaj Scheduled Task
`python manage.py purge_demo_visitors` (np. raz dziennie).

### Przed i po deployu
- ☐ CI zielone na PR (`ci.yml`, `security.yml`)
- ☐ backup bazy prod sprzed deployu — nowa tabela, nie obowiązkowy
- ☐ po deployu: `/healthz` zwraca `{"status": "ok"}`
- ☐ kroki z sekcji 2 wykonane na demo

## 4. Plan wycofania
1. Szybko bez deployu: ustaw `DEMO_VISITOR_GATE=0` w Coolify i zrestartuj — bramka znika.
2. Kod: Coolify → zasób → **Deployments** → poprzedni deployment → **Redeploy** (albo revert PR).
3. Migracja: `python manage.py migrate warehouse 0008_alter_location_capacity_and_more` przed
   wycofaniem kodu (usuwa tabelę odwiedzających).
4. Weryfikacja po wycofaniu: `/healthz`, „Wejdź jako demo”, lista HU.
