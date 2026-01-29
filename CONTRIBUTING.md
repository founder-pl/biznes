# 🤝 Wytyczne dla kontrybutorów

Dziękujemy za zainteresowanie rozwojem projektu **Biznes**! Ten dokument zawiera informacje, jak możesz pomóc.

## Jak pomóc?

### 1. Zgłaszanie błędów

Jeśli znajdziesz błąd:

1. Sprawdź, czy błąd nie został już zgłoszony w [Issues](https://github.com/softreck/biznes/issues)
2. Utwórz nowy issue z opisem:
   - Kroki do reprodukcji
   - Oczekiwane zachowanie
   - Faktyczne zachowanie
   - Wersja Pythona i systemu operacyjnego

### 2. Propozycje funkcjonalności

Masz pomysł na nową funkcję?

1. Utwórz issue z tagiem `enhancement`
2. Opisz:
   - Problem, który funkcja rozwiązuje
   - Proponowane rozwiązanie
   - Alternatywy, które rozważałeś

### 3. Ulepszanie dokumentacji

Dokumentacja zawsze może być lepsza:

- Poprawianie błędów językowych
- Dodawanie przykładów
- Tłumaczenia (docelowo: EN)
- Rozszerzanie słownika pojęć

### 4. Tworzenie nowych scenariuszy

Gra potrzebuje więcej scenariuszy branżowych:

- SaaS B2B
- E-commerce
- Hardware startup
- Fintech
- Healthtech

## Konfiguracja środowiska

```bash
# Klonowanie
git clone https://github.com/softreck/biznes.git
cd biznes

# Wirtualne środowisko
python -m venv venv
source venv/bin/activate  # Linux/macOS
# lub: venv\Scripts\activate  # Windows

# Instalacja w trybie deweloperskim
pip install -e ".[dev]"

# Weryfikacja
pytest
```

## Standardy kodu

### Formatowanie

Używamy **Black** i **isort**:

```bash
# Formatowanie
black src/
isort src/

# Sprawdzenie (bez zmian)
black src/ --check
isort src/ --check
```

### Typy

Projekt używa type hints. Sprawdzaj z **mypy**:

```bash
mypy src/
```

### Testy

Uruchom testy przed każdym PR:

```bash
pytest
pytest --cov=biznes  # z pokryciem
```

### Nazewnictwo

- Funkcje i zmienne: `snake_case`
- Klasy: `PascalCase`
- Stałe: `UPPER_SNAKE_CASE`
- Komendy gry: po polsku (`miesiac`, `ryzyko`)
- Dokumentacja: po polsku

## Struktura projektu

```
biznes/
├── src/biznes/
│   ├── __init__.py      # Wersja, main()
│   ├── shell.py         # Interfejs CLI (cmd.Cmd)
│   ├── core/
│   │   └── models.py    # Dataclasses
│   └── scenarios/
│       └── engine.py    # Logika scenariuszy
├── data/
│   └── game_config.yaml # Konfiguracja gry
├── docs/                # Dokumentacja
├── tests/               # Testy
└── pyproject.toml       # Packaging
```

## Proces Pull Request

1. **Fork** repozytorium
2. Utwórz **branch** (`git checkout -b feature/moja-funkcja`)
3. Wprowadź zmiany
4. Uruchom testy (`pytest`)
5. Sformatuj kod (`black src/ && isort src/`)
6. **Commit** (`git commit -m 'Dodaj: opis zmian'`)
7. **Push** (`git push origin feature/moja-funkcja`)
8. Utwórz **Pull Request**

### Konwencja commitów

```
Dodaj: nowa funkcjonalność
Napraw: opis naprawionego błędu
Zmień: modyfikacja istniejącej funkcji
Usuń: usunięta funkcjonalność
Docs: zmiany w dokumentacji
Test: dodanie/modyfikacja testów
```

## Dodawanie nowych scenariuszy

### Format zdarzenia w YAML

```yaml
events:
  positive:
    - name: "nazwa_zdarzenia"
      description: "Opis po polsku"
      probability: 0.1  # 10% szans
      effect:
        mrr_multiplier: 1.2  # +20% MRR
        cash_bonus: 10000
      min_stage: "SEED"  # Minimalna faza
```

### Format decyzji

```yaml
decisions:
  - type: "typ_decyzji"
    trigger: "nazwa_zdarzenia"
    description: "Opis sytuacji"
    options:
      - text: "Opcja 1"
        effect:
          cash: -5000
          mrr_multiplier: 1.1
      - text: "Opcja 2"
        effect:
          equity_dilution: 0.05
```

## Dodawanie modułów edukacyjnych

Nowe moduły nauki dodawaj w `shell.py`:

```python
def _learn_nowy_temat(self):
    """Moduł nauki o nowym temacie."""
    self._print_box("TEMAT: Nazwa tematu", Colors.HEADER)
    print("""
Treść edukacyjna...
    """)
```

I zarejestruj w mapie tematów:

```python
topics = {
    # ...
    'nowy': self._learn_nowy_temat,
}
```

## Licencja

Wysyłając Pull Request, zgadzasz się na udostępnienie swojego kodu na licencji MIT.

## Kontakt

- Issues: [GitHub Issues](https://github.com/softreck/biznes/issues)
- Dyskusje: [GitHub Discussions](https://github.com/softreck/biznes/discussions)

## Code of Conduct

Bądź uprzejmy i pomocny. Szanuj innych kontrybutorów. Konstruktywna krytyka jest mile widziana, destrukcyjna nie.

---

Dziękujemy za wkład w rozwój projektu! 🚀
