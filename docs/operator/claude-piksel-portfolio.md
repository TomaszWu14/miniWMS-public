# claude/piksel-portfolio — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/piksel-portfolio` |
| PR | jeszcze nie utworzony |
| Data | 2026-10-24 |
| Ryzyko | niskie — tylko dodanie niewidocznego znacznika `<img>` do dwóch szablonów bazowych, bez zmian logiki/danych |

## 1. Co zmieniono
- Każdy ekran demo (zalogowany, logowanie, panel „przedstaw się" przed demo, skaner) wysyła
  teraz jedno niewidoczne żądanie GET do `https://portfolio.twapp.pl/px/miniwms` — portfolio
  liczy to jako obejrzenie ekranu demo. Nic się nie zmienia dla użytkownika (piksel ma
  `width="1" height="1" hidden`, nie widać go).
- Zmiany techniczne: dodano `<img>` w `warehouse/templates/warehouse/base.html` (jedna
  linia, tuż przed `</body>`) i w `warehouse/templates/warehouse/scanner/base.html` (jedna
  linia, tuż przed `</body>`) — to dwa jedyne szablony bazowe w repo, każdy ekran dziedziczy
  z jednego z nich, więc żaden ekran nie policzy się dwa razy. Brak CSP w repo (brak nagłówka
  `Content-Security-Policy`, meta tagów CSP czy wpisu w `Caddyfile`) — nie było nic do
  poluzowania. Dodano test `TrackingPixelTests` w `warehouse/tests_security_headers.py`.

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | — (niezalogowany) | `/login/` | Otwórz DevTools → Network, odśwież stronę | widoczne żądanie GET do `portfolio.twapp.pl/px/miniwms` |
| 2 | `demo_operator` (Operator) | dashboard po zalogowaniu | Otwórz DevTools → Network, odśwież stronę | widoczne żądanie GET do `portfolio.twapp.pl/px/miniwms` |
| 3 | `demo_operator` (Operator) | `/skaner/` | Otwórz DevTools → Network, odśwież stronę | widoczne żądanie GET do `portfolio.twapp.pl/px/miniwms` |

## 3. Checklista wdrożenia

### Migracje — na KAŻDEJ bazie
Nie dotyczy — brak migracji w tym branchu (tylko szablony HTML i test).

### Zmienne środowiskowe
Nie dotyczy — brak nowych zmiennych środowiskowych.

### Przed i po deployu
- ☐ CI zielone na PR (`ci.yml`, `security.yml`)
- nie dotyczy: backup bazy prod (brak migracji)
- ☐ po deployu: `/healthz` zwraca `{"status": "ok"}`
- ☐ kroki z sekcji 2 wykonane na prod (albo na demo pod `miniwms.twapp.pl`)

## 4. Plan wycofania
1. Kod: Coolify → zasób → **Deployments** → poprzedni deployment → **Redeploy**
   (albo revert PR na `main`).
2. Migracje: nie dotyczy.
3. Zmienne środowiskowe: nie dotyczy.
4. Weryfikacja po wycofaniu: `/healthz`, logowanie — piksel po prostu przestaje się
   wysyłać, nic więcej się nie zmienia.
