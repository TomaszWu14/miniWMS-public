# docs: README po angielsku i odznaka CI na górze — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-readme-en` |
| PR | jeszcze nie utworzony |
| Data | 2026-10-21 |
| Ryzyko | niskie — tylko dokumentacja, aplikacja bez zmian |

## 1. Co zmieniono
- Nowy `README.en.md` — pełne tłumaczenie README (problem, demo, zrzuty, uruchomienie,
  stack, bezpieczeństwo, zakres, kontekst) z dopiskiem, że interfejs i dokumenty analityczne
  są po polsku; polskie nazwy przycisków z tłumaczeniem w nawiasie.
- `README.md`: odznaka CI przeniesiona spod „Jak uruchomić” pod tytuł, przełącznik języka
  PL / EN.
- Zmiany techniczne bez wpływu na UI: nie dotyczy.

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | nie dotyczy | strona repo na GitHubie (gałąź PR) | otworzyć README, kliknąć „English version” | otwiera się `README.en.md`, logo, GIF i zrzuty się wyświetlają |
| 2 | nie dotyczy | `README.en.md` | kliknąć linki do docs/, wideo, SECURITY.md, LICENSE | wszystkie prowadzą do istniejących plików |
| 3 | nie dotyczy | `README.md` | spojrzeć na górę strony | odznaka CI pod tytułem, zielona |

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
- ☐ po deployu: nie dotyczy (zmiana tylko w dokumentacji)

## 4. Plan wycofania
1. Kod: revert PR na `main`.
2. Migracje: nie dotyczy.
3. Zmienne środowiskowe: nie dotyczy.
4. Weryfikacja po wycofaniu: README wyświetla się poprawnie.
