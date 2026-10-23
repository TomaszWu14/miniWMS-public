# Ukrycie adresu e-mail właściciela przed botami — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-hide-email` |
| PR | draft (link w opisie PR) |
| Data | 2026-10-23 |
| Ryzyko | niskie — zmiana jednego tekstu w klauzuli RODO i jednego testu; brak zmian w logice, bazie i konfiguracji |

## 1. Co zmieniono
- W klauzuli RODO na stronie „przedstaw się” adres kontaktowy jest zapisany jako
  `tomasz.wierzbowski [at] op.pl` zamiast jawnego adresu z `@`, żeby proste boty zbierające
  adresy go nie wyciągały. Człowiek nadal widzi adres i może go użyć.
- Technicznie: test `tests_visitor_gate.py` sprawdza, że strona bramki zawiera formę z „[at]”
  i nie zawiera adresu z `@`. Jawny adres nie występował już nigdzie indziej w repo.

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | brak | `/demo/przedstaw-sie/` | przeczytać klauzulę, „Ctrl+U” i poszukać `@op.pl` | w klauzuli widać `tomasz.wierzbowski [at] op.pl`; w źródle strony brak `@op.pl` |

## 3. Checklista wdrożenia

### Migracje — na KAŻDEJ bazie
| Baza | Polecenie | Wykonano (kto, kiedy) |
|---|---|---|
| dev (lokalny SQLite) | `python manage.py migrate` | nie dotyczy |
| test (baza testów) | tworzona automatycznie przez `manage.py test` | ☑ testy zielone (`manage.py test`: 272 testy OK, 2 skipped) |
| demo (jeśli wdrożone) | automatycznie w `entrypoint.sh` przy deployu | nie dotyczy |
| prod (PostgreSQL, Coolify) | automatycznie w `entrypoint.sh` przy deployu | nie dotyczy |

Nowe migracje w tym branchu: brak. Odwracalne: nie dotyczy.

### Zmienne środowiskowe
Nie dotyczy (brak nowych, zmienionych ani usuniętych).

### Przed i po deployu
- ☐ CI zielone na PR (`ci.yml`, `security.yml`)
- nie dotyczy: backup bazy (brak migracji)
- ☐ po deployu: `/healthz` zwraca `{"status": "ok"}`
- ☐ krok z sekcji 2 wykonany

## 4. Plan wycofania
Revert PR na `main` albo Coolify → **Deployments** → poprzedni deployment → **Redeploy**.
Migracji i zmiennych środowiskowych nie ma, więc nic więcej do cofania.
