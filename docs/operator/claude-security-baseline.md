# claude/security-baseline — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/security-baseline` |
| PR | jeszcze nie utworzony |
| Data | 2026-10-19 |
| Ryzyko | niskie — nowe nagłówki HTTP i bramki CI; brak migracji i zmian w logice magazynu |

## 1. Co zmieniono
- Brak zmian widocznych w interfejsie magazynu.
- Technicznie: aplikacja dokłada nagłówek `Permissions-Policy` (aparat tylko z własnej
  domeny — skaner działa jak dotąd; mikrofon, lokalizacja, płatności, USB wyłączone) oraz
  `Cache-Control: no-store` na odpowiedziach JSON (API skanera, `/healthz`).
- CI: `security.yml` uruchamia się na każdym PR do `main` i blokuje scalenie przy
  znalezisku (gitleaks, Bandit, Semgrep OWASP, Trivy, pip-audit); akcje przypięte do SHA,
  `permissions: contents: read` w `ci.yml`.
- Dependabot: grupy minor+patch dla pip i akcji GitHub; `SECURITY.md`; sekcja
  „Bezpieczeństwo” w README.

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | dowolne | `/login/` | DevTools → Network → nagłówki odpowiedzi | jest `Permissions-Policy: camera=(self), …` i `X-Frame-Options: DENY` |
| 2 | `demo_operator` (Operator) | skaner → „Skanuj aparatem” | zezwól na aparat | podgląd z aparatu działa jak przed zmianą |
| 3 | dowolne | `/healthz` | nagłówki odpowiedzi | `Cache-Control: no-store` |

## 3. Checklista wdrożenia

### Migracje — na KAŻDEJ bazie
| Baza | Polecenie | Wykonano (kto, kiedy) |
|---|---|---|
| dev (lokalny SQLite) | `python manage.py migrate` | ☐ |
| test (baza testów) | tworzona automatycznie przez `pytest` / `manage.py test` | ☐ testy zielone |
| demo (jeśli wdrożone) | automatycznie w `entrypoint.sh` przy deployu | ☐ sprawdzono log |
| prod (PostgreSQL, Coolify) | automatycznie w `entrypoint.sh` przy deployu | ☐ sprawdzono log |

Nowe migracje w tym branchu: brak.
Sprawdzenie: `python manage.py showmigrations warehouse` — wszystkie `[X]`.

### Zmienne środowiskowe
| Zmienna | Nowa / zmieniona / usunięta | Wartość prod | Ustawiona w Coolify |
|---|---|---|---|
| — (nie dotyczy) | | | ☐ |

### Przed i po deployu
- ☐ CI zielone na PR (`ci.yml`, `security.yml`)
- ☐ backup bazy prod sprzed deployu — nie dotyczy (brak migracji)
- ☐ po deployu: `/healthz` zwraca `{"status": "ok"}`
- ☐ kroki z sekcji 2 wykonane na prod

## 4. Plan wycofania
1. Kod: Coolify → zasób → **Deployments** → poprzedni deployment → **Redeploy**
   (albo revert PR na `main`).
2. Migracje: nie dotyczy (brak).
3. Zmienne środowiskowe: nie dotyczy.
4. Weryfikacja po wycofaniu: `/healthz`, logowanie, lista HU, skaner z aparatem.
