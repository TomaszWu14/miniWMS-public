# Monitoring gości demo v2 (firmy z listy + aktywność) — instrukcja dla operatora

| | |
|---|---|
| Branch | `claude/laughing-cray-me204b-visitor-activity` |
| PR | draft (link w opisie PR) |
| Data | 2026-10-23 |
| Ryzyko | niskie — jedna migracja dodająca 3 kolumny z wartościami domyślnymi; licznik działa tylko przy bramce demo, a każdy jego błąd trafia tylko do logu |

## 1. Co zmieniono
- **Alarm „uwaga, ta firma”**: jeśli firma gościa zawiera którąś frazę z `NTFY_WATCH_COMPANIES`
  (bez względu na wielkość liter, polskie znaki i nadmiarowe spacje), push przychodzi z priorytetem
  **urgent**, ikoną syreny i tytułem `UWAGA firma z listy: miniWMS`; treść zaczyna się od „⚠️ ”.
  Bez trafienia — zwykły push jak dotąd.
- **Aktywność gościa**: przy każdym wpisie na liście `/odwiedzajacy/` widać nowe kolumny
  **Ekrany** (ile ekranów obejrzał), **Czas** („ok. N min” od wpisu do ostatniego ekranu, „—” gdy
  nic nie oglądał) i **Najczęściej** (3 najczęstsze sekcje, np. `materialy (4), start (2)`).
- **Push „zaangażowany gość”**: gdy gość obejrzy dokładnie `NTFY_ENGAGED_VIEWS` ekranów (domyślnie
  10), przychodzi jeden push `Gosc oglada demo: miniWMS` — „Anna Nowak (ACME) obejrzał już 10 ekranów
  w miniWMS” (dla firmy z listy też z priorytetem urgent).
- **Klauzula RODO** w formularzu „przedstaw się”: dopisane, że zapisywane jest, ile i jakie ekrany
  demo gość obejrzał (bez adresu IP).
- Technicznie: ciasteczko bramki niesie teraz podpisane id wpisu (`id:<pk>`; stare ciasteczka `1`
  nadal wpuszczają, tylko aktywność się nie liczy). Nowy middleware
  `warehouse/visitor_activity.py` liczy udane (2xx) GET-y stron HTML — bez statyk, `/healthz`,
  API skanera, przekierowań i błędów. Sekcja = pierwszy segment ścieżki (`/` → `start`), max 20
  sekcji na gościa. Nowe pola `DemoVisitor`: `page_views`, `last_seen_at`, `sections` (JSON).
  Retencja 90 dni bez zmian (pola znikają razem z wpisem).

## 2. Kroki do ręcznego sprawdzenia

| # | Konto (rola) | Gdzie | Co zrobić | Oczekiwany wynik |
|---|---|---|---|---|
| 1 | — | Coolify → zmienne zasobu demo | ustawić `NTFY_WATCH_COMPANIES` (np. fraza testowa `testfirma`) i zrestartować | kontener wstaje, `/healthz` OK |
| 2 | brak (okno incognito) | demo → „Wejdź jako demo” | przedstawić się z firmą `TestFirma Sp. z o.o.` | push z syreną, priorytet urgent, tytuł „UWAGA firma z listy: miniWMS”, treść od „⚠️ ” |
| 3 | brak (nowe okno incognito) | demo | przedstawić się z inną firmą | zwykły push „Nowy gosc: miniWMS” |
| 4 | gość z kroku 3 | demo | otworzyć ok. 10 różnych ekranów (Materiały, Lokalizacje, pulpit…) | po 10. ekranie jeden push „Gosc oglada demo: miniWMS”; kolejne ekrany nie wysyłają nic |
| 5 | admin | `/odwiedzajacy/` | otworzyć listę | przy gościu z kroku 4: Ekrany ≥ 10, Czas „ok. N min”, Najczęściej — 3 sekcje |
| 6 | brak | formularz „przedstaw się” | przeczytać klauzulę | zawiera „Zapisuję też, ile i jakie ekrany wersji demonstracyjnej obejrzałeś (bez adresu IP)…” |
| 7 | — | Coolify | usunąć frazę testową z `NTFY_WATCH_COMPANIES`, wpisać docelowe frazy | — |

## 3. Checklista wdrożenia

### Migracje — na KAŻDEJ bazie
| Baza | Polecenie | Wykonano (kto, kiedy) |
|---|---|---|
| dev (lokalny SQLite) | `python manage.py migrate` | ☐ |
| test (baza testów) | tworzona automatycznie przez `manage.py test` | ☑ testy zielone (`manage.py test`: 272 testy OK, 2 skipped) |
| demo (jeśli wdrożone) | automatycznie w `entrypoint.sh` przy deployu | ☐ sprawdzono log |
| prod (PostgreSQL, Coolify) | automatycznie w `entrypoint.sh` przy deployu | ☐ sprawdzono log |

Nowe migracje w tym branchu: `warehouse/migrations/0010_demovisitor_activity.py` (3× `AddField` z
domyślną wartością / NULL). Odwracalne: tak (`migrate warehouse 0009_demovisitor` usuwa kolumny —
tracona jest tylko zebrana aktywność).
Sprawdzenie: `python manage.py showmigrations warehouse` — wszystkie `[X]`;
`python manage.py makemigrations --check --dry-run` → „No changes detected”.

### Zmienne środowiskowe
| Zmienna | Nowa / zmieniona / usunięta | Wartość prod | Ustawiona w Coolify |
|---|---|---|---|
| `NTFY_WATCH_COMPANIES` | nowa (opcjonalna; puste = brak alarmów) | frazy po przecinku, min. 2 znaki każda — prawdziwe nazwy tylko w Coolify | ☐ |
| `NTFY_ENGAGED_VIEWS` | nowa (opcjonalna; domyślnie `10`, `0` = wyłączone) | `10` | ☐ jeśli inna niż domyślna |

Zaktualizowano też: `.env.example` ☑, `.env.docker.example` nie dotyczy (zmienne dla instancji demo),
`COOLIFY.md` §11 ☑, `docker-compose.coolify.yml` ☑ (przekazuje obie zmienne do `web`).

### Przed i po deployu
- ☐ CI zielone na PR (`ci.yml`, `security.yml`)
- ☐ backup bazy demo/prod sprzed deployu — jest migracja (tylko nowe kolumny w `warehouse_demovisitor`)
- ☐ po deployu: `/healthz` zwraca `{"status": "ok"}`
- ☐ kroki z sekcji 2 wykonane na demo

## 4. Plan wycofania
1. Szybko bez deployu: `NTFY_WATCH_COMPANIES=` (puste) wyłącza alarmy, `NTFY_ENGAGED_VIEWS=0` —
   push „zaangażowany gość”; restart zasobu.
2. Migracje: `python manage.py migrate warehouse 0009_demovisitor` w kontenerze **przed**
   wycofaniem kodu.
3. Kod: Coolify → zasób → **Deployments** → poprzedni deployment → **Redeploy** (albo revert PR).
   Ciasteczka gości `id:<pk>` poprzednia wersja uzna za nieważne — goście raz jeszcze się przedstawią.
4. Weryfikacja po wycofaniu: `/healthz`, „Wejdź jako demo”, lista HU.
