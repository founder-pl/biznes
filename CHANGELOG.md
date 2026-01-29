## [1.0.3] - 2026-01-29

### Summary

refactor(docs): configuration management system

### Core

- update src/biznes/core/models.py
- update src/biznes/shell.py

### Docs

- docs: update README

### Build

- update pyproject.toml

### Other

- update src/biznes/__pycache__/__init__.cpython-313.pyc
- update src/biznes/__pycache__/shell.cpython-313.pyc


## [1.0.2] - 2026-01-29

### Summary

feat(other): add configuration, formatting, cli

### Docs

- docs: update README

### Config

- config: update goal.yaml

### Other

- update .gitignore
- update img.png


## [1.0.1] - 2026-01-29

### Summary

feat(docs): configuration management system

### Core

- update src/biznes/__init__.py
- update src/biznes/__main__.py
- update src/biznes/core/__init__.py
- update src/biznes/core/models.py
- update src/biznes/legal/__init__.py
- update src/biznes/scenarios/__init__.py
- update src/biznes/scenarios/engine.py
- update src/biznes/shell.py
- update src/biznes/utils/__init__.py

### Docs

- docs: update CONTRIBUTING.md
- docs: update README
- docs: update EQUITY.md
- docs: update GAMEPLAY.md
- docs: update GLOSSARY.md
- docs: update INSTALL.md
- docs: update LEGAL_FORMS.md
- docs: update PROTECTIONS.md

### Test

- update tests/__pycache__/conftest.cpython-313-pytest-9.0.2.pyc
- update tests/__pycache__/test_biznes.cpython-313-pytest-9.0.2.pyc
- update tests/conftest.py
- update tests/test_biznes.py

### Build

- update pyproject.toml

### Config

- config: update goal.yaml

### Other

- update .idea/.gitignore
- update .idea/biznes.iml
- update .idea/inspectionProfiles/Project_Default.xml
- update .idea/inspectionProfiles/profiles_settings.xml
- update .idea/misc.xml
- update .idea/modules.xml
- update .idea/vcs.xml
- build: update Makefile
- config: update game_config.yaml
- update src/biznes/__pycache__/__init__.cpython-313.pyc
- ... and 1 more


# Changelog

Wszystkie znaczące zmiany w projekcie będą dokumentowane w tym pliku.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/),
projekt stosuje [Semantic Versioning](https://semver.org/lang/pl/).

## [1.0.0] - 2025-01-29

### Dodane

#### Mechanika gry
- Interaktywna konsola z komendami w języku polskim
- 8-etapowa konfiguracja nowej gry
- Symulacja miesięczna z automatycznym wzrostem
- System zdarzeń losowych (8 pozytywnych, 12 negatywnych)
- Drzewa decyzyjne (7 typów decyzji)
- Analiza ryzyka z rekomendacjami
- 3 poziomy trudności (łatwy, normalny, trudny)

#### Modele biznesowe
- Formy prawne: PSA, Sp. z o.o., JDG
- Vesting z konfigurowalnymi parametrami
- Good/bad leaver z precyzyjnymi definicjami
- Tag-along / drag-along
- Anti-dilution (full ratchet, weighted average)
- Liquidation preference
- ESOP pool

#### Finanse
- Śledzenie MRR/ARR
- Burn rate i runway
- Wycena firmy (5x ARR)
- Rundy inwestycyjne z rozwodnieniem
- Cash flow management

#### Weryfikacja partnera
- Integracja z KRS (ekrs.ms.gov.pl)
- Rejestry dłużników (BIG, KRD, ERIF)
- System red flags
- Checklista weryfikacyjna

#### Edukacja
- 8 modułów nauki (formy, vesting, leaver, tagdrag, ip, partner, mvp, equity)
- Słownik 18 pojęć startupowych
- Szczegółowe objaśnienia podczas gry

#### Persistence
- Zapis/odczyt stanu gry (YAML)
- Eksport konfiguracji do YAML
- Automatyczny zapis po decyzjach

#### Dokumentacja
- README.md z pełnym opisem
- docs/INSTALL.md - instrukcja instalacji
- docs/GAMEPLAY.md - przewodnik po grze
- docs/GLOSSARY.md - słownik pojęć
- docs/LEGAL_FORMS.md - porównanie form prawnych
- docs/EQUITY.md - podział equity
- docs/PROTECTIONS.md - zabezpieczenia prawne

#### Infrastruktura
- Packaging z pyproject.toml
- Entry point `biznes`
- Kolorowy output terminalowy
- Obsługa polskich znaków (UTF-8)

### Techniczne

- Python 3.8+
- Zależności: pyyaml>=6.0
- Dev: pytest, black, isort, mypy
- Struktura: src layout

## [Unreleased]

### Planowane
- Tryb multiplayer (symulacja negocjacji)
- Więcej scenariuszy branżowych
- Import danych z rzeczywistych spółek
- Graficzny interfejs (TUI z Rich/Textual)
- API do integracji z narzędziami prawnymi
- Lokalizacja EN
