# 🎮 Biznes - Symulator Startupu dla Founderów

Edukacyjna gra konsolowa symulująca zakładanie i prowadzenie startupu w Polsce. Naucz się podejmować kluczowe decyzje biznesowe, prawne i finansowe w bezpiecznym środowisku.
![img.png](img.png)

## 🎯 Cel gry

Gra **Biznes** ma na celu edukację osób planujących założenie startupu poprzez praktyczne symulowanie:

- Weryfikacji potencjalnego wspólnika
- Negocjacji podziału equity
- Wyboru formy prawnej (PSA vs Sp. z o.o.)
- Tworzenia zabezpieczeń prawnych (vesting, good/bad leaver, tag-along)
- Zarządzania finansami i runway
- Reagowania na losowe zdarzenia rynkowe
- Podejmowania strategicznych decyzji

## 🚀 Instalacja

```bash
# Klonowanie repozytorium
git clone https://github.com/softreck/biznes.git
cd biznes

# Instalacja w trybie deweloperskim
pip install -e .

# Lub bezpośrednie uruchomienie
python -m biznes
```

## 📖 Jak grać

### Uruchomienie

```bash
# Po instalacji
biznes

# Lub bezpośrednio
python -m biznes.shell
```

### Podstawowe komendy

| Komenda | Opis |
|---------|------|
| `start` | Rozpocznij nową grę |
| `status` | Pokaż aktualny stan firmy |
| `miesiac` | Przejdź do następnego miesiąca |
| `ryzyko` | Analiza ryzyka |
| `finanse` | Szczegóły finansowe |
| `equity` | Podział udziałów (cap table) |
| `umowa` | Status umowy wspólników |
| `nauka` | Materiały edukacyjne |
| `slownik` | Słownik pojęć startupowych |
| `zapisz` | Zapisz stan gry |
| `eksport` | Eksportuj konfigurację do YAML |
| `pomoc` | Wyświetl pomoc |
| `wyjscie` | Zakończ grę |


```bash
============================================================                                                                                                                                                                                            
  PODSUMOWANIE KONFIGURACJI
============================================================
┌─────────────────────────────────────────────────┐
│ TWOJA GRA                                       │
├─────────────────────────────────────────────────┤
│ Gracz: f1 (technical)                           │
│ Partner: f2                                     │
│                                                 │
│ Forma prawna: PSA                               │
│ Equity: Ty 56.0% / Partner 34.0% / ESOP 10.0%   │
│ Vesting: 48 mies. z 12 mies. cliff              │
│                                                 │
│ Kapitał startowy: 0 PLN                         │
│ MVP: Tak                                        │
│                                                 │
│ Trudność: normal                                │
│ Zdarzenia losowe: Włączone                      │
└─────────────────────────────────────────────────┘

⚠️  BRAKUJĄCE ZABEZPIECZENIA:                                                                                                                                                                                                                           
   • Klauzula poufności (NDA)
   • Procedura rozwiązywania impasów

✓ Gra rozpoczęta! Wpisz 'status' aby zobaczyć stan firmy.                                                                                                                                                                                               
  Wpisz 'miesiac' aby przejść do następnego miesiąca.
```

## 🎓 Czego się nauczysz?

### Formy prawne
- **PSA (Prosta Spółka Akcyjna)** - idealna dla startupów z equity
- **Sp. z o.o.** - klasyczna forma dla bootstrappingu

### Podział equity
- Wycena MVP metodą kosztową
- Fair podział między technical i business co-founderami
- ESOP pool dla przyszłych pracowników

### Zabezpieczenia prawne
- **Vesting** - stopniowe nabywanie udziałów (4 lata, 1 rok cliff)
- **Good/Bad leaver** - warunki odejścia wspólnika
- **Tag-along** - prawo przyłączenia do sprzedaży
- **Drag-along** - prawo pociągnięcia do sprzedaży
- **NDA** - klauzula poufności
- **Non-compete** - zakaz konkurencji

### Weryfikacja partnera
- Sprawdzanie w KRS (ekrs.ms.gov.pl)
- Rejestry dłużników (BIG, KRD, ERIF)
- Red flags do rozpoznania

### Finanse startupu
- MRR (Monthly Recurring Revenue)
- Burn rate i runway
- Wycena firmy
- Rundy inwestycyjne i rozwodnienie

## 🎲 Mechanika gry

### Etapy konfiguracji

1. **Dane gracza** - Twoja rola (technical/business)
2. **MVP** - Czy masz gotowy prototyp? Wycena.
3. **Partner** - Weryfikacja, co wnosi
4. **Equity** - Podział udziałów z rekomendacją
5. **Forma prawna** - PSA czy Sp. z o.o.?
6. **Zabezpieczenia** - Klauzule w umowie wspólników
7. **Cele** - MRR, klienci, runway
8. **Symulacja** - Trudność, zdarzenia losowe

### Symulacja miesięczna

Każdy miesiąc:
- Automatyczny wzrost klientów i MRR
- Spalanie gotówki (burn rate)
- Losowe zdarzenia (pozytywne i negatywne)
- Aktualizacja vestingu
- Sprawdzanie warunków sukcesu/porażki

### Zdarzenia losowe

**Pozytywne:**
- Viral marketing
- Strategiczny partner
- Enterprise klient
- Nagroda branżowa

**Negatywne:**
- Konkurent z dużym funding
- Kluczowy pracownik odchodzi
- Konflikt między founderami
- MVP nie spełnia oczekiwań
- Problem z płynnością

## 📁 Struktura projektu

```
biznes/
├── src/biznes/
│   ├── __init__.py
│   ├── shell.py           # Główny interfejs
│   ├── core/
│   │   ├── __init__.py
│   │   └── models.py      # Modele danych
│   └── scenarios/
│       ├── __init__.py
│       └── engine.py      # Silnik scenariuszy
├── data/
│   └── game_config.yaml   # Pełna konfiguracja gry
├── templates/
├── pyproject.toml
└── README.md
```

## 📊 Plik konfiguracyjny YAML

Gra zapisuje wszystkie parametry do pliku YAML, który może służyć jako:
- Dokumentacja założeń startupu
- Podstawa do dyskusji z prawnikiem
- Materiał do negocjacji z partnerem

Przykład eksportowanej konfiguracji:

```yaml
player:
  name: Jan
  role: technical

mvp:
  has_mvp: true
  hours_invested: 400
  hourly_rate: 150
  external_costs: 10000
  calculated_value: 70000

partner:
  name: Anna
  capital: 20000
  customers: 5
  industry_experience_years: 8
  verified:
    krs: true
    debts: true

equity:
  player_percentage: 55
  partner_percentage: 35
  esop_pool: 10

legal:
  preferred_form: psa
  vesting_months: 48
  cliff_months: 12
  protections:
    tag_along: true
    good_bad_leaver: true
    ip_protection: true
    non_compete: true
    non_compete_months: 12

targets:
  6_months:
    mrr: 10000
    customers: 50
  12_months:
    mrr: 30000
    customers: 150
```

## 🏆 Warunki zwycięstwa

- Osiągnięcie zdefiniowanych celów MRR i liczby klientów
- Zachowanie dodatniego runway
- Uniknięcie bankructwa

## 💀 Warunki porażki

- Gotówka spada poniżej zera
- Bankructwo firmy

## 🛠️ Rozwój

```bash
# Instalacja zależności deweloperskich
pip install -e ".[dev]"

# Testy
pytest

# Formatowanie kodu
black src/
isort src/

# Sprawdzenie typów
mypy src/
```

## 📜 Licencja

MIT License

## 🙏 Podziękowania

Gra powstała na bazie wiedzy o polskim prawie spółek, mechanizmach equity w startupach i doświadczeniach founders z ekosystemu polskich startupów.

---

**Powodzenia w budowaniu Twojego startupu!** 🚀
