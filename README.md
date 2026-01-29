# 🚀 BIZNES - Symulator Startupu v2.0

Interaktywna gra edukacyjna o zakładaniu firmy w Polsce. Naucz się vestingu, umów wspólników, form prawnych i finansów startupowych.

![img.png](img.png)

## ✨ Co nowego w v2.0

- **Interaktywne menu akcji** - każdego miesiąca widzisz co możesz zrobić
- **Konsekwencje decyzji** - przed każdą akcją widzisz korzyści i ryzyka
- **Blokady z wyjaśnieniem** - dlaczego nie możesz wykonać danej akcji
- **Dynamiczny vesting** - śledzenie cliff i vested udziałów
- **Losowe zdarzenia** - realistyczne sytuacje biznesowe

## 🎮 Szybki start

```bash
# Instalacja (wersja tekstowa)
pip install -e .

# Instalacja z TUI (nawigacja strzałkami)
pip install -e ".[tui]"

# Uruchomienie - wersja tekstowa
biznes

# Uruchomienie - wersja TUI (strzałki, Enter, bez pisania)
biznes-tui
```

### 🖥️ Tryb TUI (Textual)

Nowy tryb z pełną nawigacją klawiaturą:
- **↑↓** - wybór opcji
- **Enter** - zatwierdź
- **Esc** - wróć
- **M/S/F/E/H/Q** - skróty klawiszowe

## 📋 Komendy

| Komenda | Opis |
|---------|------|
| `start` | Nowa gra z konfiguracją |
| `miesiac` | Następny miesiąc + menu akcji (max 2 akcje) |
| `akcje` | Pokaż dostępne akcje |
| `historia` | Historia decyzji i zdarzeń |
| `status` | Stan firmy |
| `finanse` | Szczegóły finansowe |
| `equity` | Cap table |
| `ryzyko` | Analiza zagrożeń |
| `nauka` | Materiały edukacyjne |
| `slownik` | Słownik pojęć |

## 🎯 Przykład rozgrywki

```
biznes> start

ETAP 1/6: Twoje dane
Twoje imię [Founder]: Jan

Twoja rola?
  1. Technical (programista)
     → Konsekwencja: Twój czas = wartość MVP
  2. Business (sprzedaż)
     → Konsekwencja: Potrzebujesz technicznego co-foundera

...

════════════════════════════════════════════════════════════
  MIESIĄC 1
════════════════════════════════════════════════════════════

📊 SYTUACJA:
   Gotówka: 10,000 PLN
   MRR: 0 PLN | Klienci: 0
   Runway: 2 mies

────────────────────────────────────────────────────────────
  DOSTĘPNE AKCJE
────────────────────────────────────────────────────────────

⚖️ PRAWNE:
  1. ✓ Załóż spółkę [ZALECANE]
     Zarejestruj PSA w KRS
  2. ✓ Podpisz umowę wspólników (SHA) ⚠️ BEZ UMOWY RYZYKUJESZ WSZYSTKO!
     Formalna umowa regulująca prawa founderów

🔧 PRODUKT:
  3. ✓ Rozwijaj MVP [ZALECANE]
     Kontynuuj prace nad produktem
```

## 📚 Czego się nauczysz

- **Formy prawne**: PSA vs Sp. z o.o. - kiedy która
- **Vesting**: 48 miesięcy, cliff 12 miesięcy, dlaczego to ważne
- **Good/Bad leaver**: Ochrona przed odejściem partnera
- **Tag-along/Drag-along**: Prawa przy sprzedaży
- **Wycena MVP**: Metoda kosztowa (godziny × stawka)
- **Podział equity**: Czynniki wpływające na udziały
- **Weryfikacja partnera**: KRS, rejestry dłużników

## 🎲 Mechanika gry

Każdy miesiąc:
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

## 🔧 Wymagania

- Python 3.8+
- Terminal z obsługą UTF-8 i kolorów ANSI

## 📄 Licencja

MIT License - Softreck 2025

## 🤝 Wsparcie

Masz pytania? Otwórz issue na GitHubie!
