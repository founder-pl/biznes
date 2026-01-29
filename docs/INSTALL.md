# 📦 Instrukcja instalacji - Biznes

## Wymagania systemowe

- **Python**: 3.8 lub nowszy
- **System operacyjny**: Windows, macOS, Linux
- **Terminal**: z obsługą kolorów ANSI (większość nowoczesnych terminali)

## Metody instalacji

### Metoda 1: pip (zalecana)

```bash
pip install biznes
```

### Metoda 2: Z repozytorium GitHub

```bash
# Klonowanie repozytorium
git clone https://github.com/softreck/biznes.git
cd biznes

# Instalacja w trybie deweloperskim
pip install -e .
```

### Metoda 3: Z paczki zip

1. Pobierz paczkę `biznes-1.0.0.zip`
2. Rozpakuj do wybranego folderu
3. W terminalu przejdź do folderu:

```bash
cd biznes-1.0.0
pip install -e .
```

### Metoda 4: Bez instalacji

Możesz uruchomić grę bezpośrednio:

```bash
cd biznes
python -m biznes.shell
```

## Uruchomienie

Po instalacji:

```bash
biznes
```

Lub bezpośrednio z repozytorium:

```bash
python -m biznes
```

## Weryfikacja instalacji

```bash
# Sprawdź wersję
biznes --version

# Lub uruchom i wpisz 'pomoc'
biznes
> pomoc
```

## Rozwiązywanie problemów

### "Command not found: biznes"

Upewnij się, że ścieżka do skryptów Pythona jest w PATH:

```bash
# Linux/macOS
export PATH="$HOME/.local/bin:$PATH"

# Windows (PowerShell)
$env:PATH += ";$env:APPDATA\Python\Python3x\Scripts"
```

### Brak kolorów w terminalu

Gra używa kodów ANSI. W Windows uruchom PowerShell lub Windows Terminal (nie klasyczny CMD).

### Błąd "ModuleNotFoundError: yaml"

Zainstaluj wymaganą zależność:

```bash
pip install pyyaml
```

### Problem z kodowaniem polskich znaków

Ustaw kodowanie UTF-8:

```bash
# Linux/macOS
export LANG=pl_PL.UTF-8

# Windows (PowerShell)
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

## Instalacja deweloperska

Dla osób chcących rozwijać grę:

```bash
# Pełna instalacja z narzędziami deweloperskimi
pip install -e ".[dev]"

# Weryfikacja
pytest                    # Uruchom testy
black src/ --check       # Sprawdź formatowanie
mypy src/                # Sprawdź typy
```

## Aktualizacja

```bash
# Z pip
pip install --upgrade biznes

# Z repozytorium
git pull
pip install -e .
```

## Dezinstalacja

```bash
pip uninstall biznes
```

## Struktura plików po instalacji

```
~/.biznes_saves/          # Zapisane stany gry
├── save_001.yaml
├── save_002.yaml
└── ...

~/biznes_exports/         # Wyeksportowane konfiguracje
├── config_2024-01-15.yaml
└── ...
```
