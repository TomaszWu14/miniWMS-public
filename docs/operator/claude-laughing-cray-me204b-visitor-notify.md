# Powiadomienie push (ntfy) o nowym gościu demo — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-visitor-notify` |
| PR | draft (link w opisie PR) |
| Data | 2026-10-23 |
| Ryzyko | niskie — bez `NTFY_URL` nic się nie zmienia (no-op); wysyłka w tle, błąd ntfy nie blokuje wejścia do demo |

## 1. Co zmieniono
- Po każdym **poprawnym** wypełnieniu formularza „przedstaw się” (bramka demo) aplikacja wysyła
  powiadomienie push na telefon (aplikacja **ntfy**): treść `Anna Nowak (ACME) wszedł do miniWMS`,
  tytuł `Nowy gosc: miniWMS`, priorytet wysoki, ikonka dzwonka. Odrzucony formularz (błędne dane,
  brak zgody, pole-pułapka) nie wysyła nic.
- Klauzula RODO w formularzu: zamiast „…i nikomu ich nie przekazuję.” jest informacja, że o każdej
  wizycie (imię, nazwisko, firma) właściciel dostaje powiadomienie przez usługę ntfy; poza tym danych
  nikomu nie przekazuje.
- Technicznie: moduł `warehouse/visitor_notify.py` (HTTP POST przez `urllib` ze stdlib, wątek w tle,
  timeout 5 s, treść przycięta do 300 znaków, błąd → ostrzeżenie w logu). Nowe zmienne `NTFY_URL`,
  `NTFY_TOKEN` (`config/settings/base.py`, przekazane w `docker-compose.coolify.yml`). Bez nowych zależności.

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | — | aplikacja ntfy na telefonie | zasubskrybować temat z `NTFY_URL` | temat na liście |
| 2 | brak (świeże okno incognito) | demo → „Wejdź jako demo” | wypełnić formularz poprawnie, zaznaczyć zgodę | wejście na pulpit + w ciągu kilku sekund push „Imię Nazwisko (Firma) wszedł do miniWMS” |
| 3 | brak (nowe okno incognito) | formularz | wysłać bez zgody / z 1-literowym nazwiskiem | błąd formularza, **brak** powiadomienia |
| 4 | brak | formularz | przeczytać klauzulę RODO | zawiera zdanie o powiadomieniu przez ntfy |
| 5 | — | Coolify → logi `web` | (opcjonalnie) ustawić błędny `NTFY_URL`, wejść jak w kroku 2 | wejście działa; w logu ostrzeżenie „Nie wysłano powiadomienia ntfy…” |

## 3. Checklista wdrożenia

### Migracje — na KAŻDEJ bazie
| Baza | Polecenie | Wykonano (kto, kiedy) |
|---|---|---|
| dev (lokalny SQLite) | nie dotyczy — brak migracji | ☐ |
| test (baza testów) | tworzona automatycznie przez `manage.py test` | ☑ testy zielone (`manage.py test`: 251 testów OK, 2 skipped) |
| demo (jeśli wdrożone) | nie dotyczy — brak migracji | ☐ |
| prod (PostgreSQL, Coolify) | nie dotyczy — brak migracji | ☐ |

Nowe migracje w tym branchu: brak. Odwracalne: nie dotyczy.
Sprawdzenie: `python manage.py makemigrations --check --dry-run` → „No changes detected”.

### Zmienne środowiskowe
| Zmienna | Nowa / zmieniona / usunięta | Wartość prod | Ustawiona w Coolify |
|---|---|---|---|
| `NTFY_URL` | nowa (opcjonalna; puste = wyłączone) | na demo: `https://ntfy.sh/<tajny-temat>` (trudny do zgadnięcia) | ☐ |
| `NTFY_TOKEN` | nowa (opcjonalna) | tylko dla serwera ntfy z kontrolą dostępu | ☐ jeśli dotyczy |

Zaktualizowano też: `.env.example` ☑, `.env.docker.example` nie dotyczy (zmienna dla instancji demo),
`COOLIFY.md` §11 (instancja demo) ☑, `docker-compose.coolify.yml` ☑ (przekazuje obie zmienne do `web`).

### Przed i po deployu
- ☐ CI zielone na PR (`ci.yml`, `security.yml`)
- ☐ backup bazy prod — nie dotyczy (brak migracji)
- ☐ po deployu: `/healthz` zwraca `{"status": "ok"}`
- ☐ kroki z sekcji 2 wykonane na demo

## 4. Plan wycofania
1. Szybko bez deployu: usuń/opróżnij `NTFY_URL` w Coolify i zrestartuj — powiadomienia znikają.
2. Kod: Coolify → zasób → **Deployments** → poprzedni deployment → **Redeploy** (albo revert PR).
3. Migracje: nie dotyczy.
4. Weryfikacja po wycofaniu: `/healthz`, „Wejdź jako demo”, lista HU.
