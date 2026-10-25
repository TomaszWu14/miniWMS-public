# claude/laughing-cray-me204b-przepustka-portfolio — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-przepustka-portfolio` |
| PR | jeszcze nie utworzony |
| Data | 2026-10-25 |
| Ryzyko | niskie — zmiana tylko w bramce gościa demo; każdy błąd portfolio = dotychczasowy formularz |

## 1. Co zmieniono
- Rekruter, który przedstawił się w portfolio (ciasteczko `gosc` na `.twapp.pl`), wchodzi do
  demo bez formularza „przedstaw się”.
- Strona formularza bramki nie ładuje już piksela portfolio `/px/miniwms` (sam widok
  formularza nie wywołuje pusha „wszedł bez przedstawienia się”).
- Technicznie: nowy moduł `warehouse/portfolio_pass.py` — backend pyta
  `GET {PORTFOLIO_URL}/api/gosc` (tylko ciasteczko `gosc`, timeout 2 s, bez przekierowań;
  liczy się wyłącznie status 200). Wynik pozytywny w cache procesu ok. 10 min po hashu tokenu,
  błąd sieci 30 s. Przepustka nie zapisuje `DemoVisitor` i nie wysyła pusha ntfy (robi to
  portfolio), więc aktywność tych gości nie jest liczona w `/odwiedzajacy/`.
- Nowe ustawienia: `PORTFOLIO_URL` (musi być `https://`), `PORTFOLIO_PASS`.
- Wymaga endpointu `/api/gosc` w portfolio (osobny wycinek). Bez niego: zwykła bramka.

## 2. Kroki do ręcznego sprawdzenia
| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | — (przeglądarka po przedstawieniu się w portfolio) | `https://miniwms.twapp.pl/demo/` | Wejść z linku | Bez formularza, zalogowany na konto demo |
| 2 | — (nowa przeglądarka, bez ciasteczka `gosc`) | `/demo/` | Wejść z linku | Formularz „Przedstaw się”, w źródle strony brak `/px/miniwms` |
| 3 | — | `/login/` | Otworzyć stronę | Piksel `/px/miniwms` nadal obecny |

## 3. Checklista wdrożenia

### Migracje — na KAŻDEJ bazie
| Baza | Polecenie | Wykonano (kto, kiedy) |
|---|---|---|
| dev (lokalny SQLite) | `python manage.py migrate` | nie dotyczy (brak migracji) |
| test (baza testów) | tworzona automatycznie przez `pytest` / `manage.py test` | ☐ testy zielone |
| demo (jeśli wdrożone) | automatycznie w `entrypoint.sh` przy deployu | nie dotyczy |
| prod (PostgreSQL, Coolify) | automatycznie w `entrypoint.sh` przy deployu | nie dotyczy |

Nowe migracje w tym branchu: brak. Odwracalne: nie dotyczy.
Sprawdzenie: `python manage.py showmigrations warehouse` — bez zmian.

### Zmienne środowiskowe
| Zmienna | Nowa / zmieniona / usunięta | Wartość prod | Ustawiona w Coolify |
|---|---|---|---|
| `PORTFOLIO_URL` | nowa (opcjonalna) | `https://portfolio.twapp.pl` (domyślna) | ☐ |
| `PORTFOLIO_PASS` | nowa (opcjonalna) | `1` (domyślna; `0` wyłącza) | ☐ |

Zaktualizowano też: `.env.example` ☑, `.env.docker.example` nie dotyczy (brak wpisów bramki), `COOLIFY.md` ☑ (krok z `DEMO_MODE`), `docker-compose.coolify.yml` ☑.

### Przed i po deployu
- ☐ CI zielone na PR (`ci.yml`, `security.yml`)
- ☐ backup bazy prod — nie dotyczy (brak migracji)
- ☐ po deployu: `/healthz` zwraca `{"status": "ok"}`
- ☐ kroki z sekcji 2 wykonane na prod (po wdrożeniu `/api/gosc` w portfolio)

## 4. Plan wycofania
1. Szybko bez deployu: w Coolify `PORTFOLIO_PASS=0` i restart — bramka działa jak wcześniej.
2. Kod: Coolify → zasób → **Deployments** → poprzedni deployment → **Redeploy**
   (albo revert PR na `main`).
3. Migracje: nie dotyczy.
4. Weryfikacja po wycofaniu: `/healthz`, `/demo/` pokazuje formularz bramki.
