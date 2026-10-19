# Polityka bezpieczeństwa

## Zgłaszanie podatności

Podatności zgłaszaj prywatnie przez GitHub: zakładka **Security → Report a vulnerability**
(Private vulnerability reporting):
<https://github.com/TomaszWu14/miniWMS-public/security/advisories/new>.

Nie zakładaj publicznego issue dla podatności. W zgłoszeniu opisz, czego dotyczy problem,
jak go odtworzyć i jaki może mieć wpływ.

Odpowiedź — najczęściej do 7 dni.

## Zakres

Wspierana jest tylko gałąź domyślna (`main`) — poprawki trafiają wyłącznie do niej.

## Co pilnuje CI

Opis skanów (gitleaks, Bandit, Semgrep, Trivy, pip-audit, Dependabot): sekcja
„Bezpieczeństwo” w [README](README.md) i [`security.yml`](.github/workflows/security.yml).
