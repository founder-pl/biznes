# 🎮 Przewodnik po grze - Biznes

## Wprowadzenie

**Biznes** to edukacyjna gra symulacyjna, która przeprowadzi Cię przez proces zakładania startupu w Polsce. Podejmiesz kluczowe decyzje dotyczące partnera biznesowego, podziału udziałów, formy prawnej i zabezpieczeń.

## Rozpoczęcie gry

Po uruchomieniu gry zobaczysz konsolę z promptem `(biznes) `. Wpisz `start`, aby rozpocząć nową grę.

```
(biznes) start
```

## Etapy konfiguracji

### Etap 1: Dane gracza

Podajesz swoje imię i wybierasz rolę:
- **technical** - Programista, CTO, odpowiedzialny za technologię
- **business** - CEO, odpowiedzialny za sprzedaż i marketing

Rola wpływa na rekomendacje dotyczące podziału equity.

### Etap 2: MVP (Minimum Viable Product)

Odpowiadasz na pytania:
1. Czy masz gotowy MVP? (tak/nie)
2. Ile godzin poświęciłeś na jego stworzenie?
3. Jaka jest Twoja stawka godzinowa?
4. Jakie były koszty zewnętrzne (serwery, domeny, licencje)?

**Wycena MVP** = godziny × stawka + koszty zewnętrzne

Przykład: 400h × 150 PLN/h + 10 000 PLN = 70 000 PLN

### Etap 3: Partner biznesowy

Definiujesz potencjalnego partnera:
- Imię partnera
- Kapitał jaki wnosi (PLN)
- Czy ma gotowych klientów?
- Doświadczenie w branży (lata)

**Weryfikacja partnera** - odpowiadasz, czy sprawdziłeś:
- KRS (Krajowy Rejestr Sądowy) - historia firm, upadłości
- Rejestry dłużników (BIG, KRD, ERIF)

Gra wskaże potencjalne red flags!

### Etap 4: Podział equity

Na podstawie wprowadzonych danych gra oblicza rekomendowany podział:
- Twój udział (%)
- Udział partnera (%)
- Pula ESOP na przyszłych pracowników (%)

Możesz zaakceptować lub zmodyfikować propozycję.

**Czynniki wpływające na rekomendację:**
- Wartość MVP
- Wnoszony kapitał
- Doświadczenie branżowe
- Gotowi klienci/kontakty

### Etap 5: Forma prawna

Wybierasz między:

| Cecha | PSA | Sp. z o.o. |
|-------|-----|------------|
| Kapitał minimalny | 1 PLN | 5 000 PLN |
| Praca jako wkład | ✅ Tak | ❌ Nie |
| Transfer udziałów | Email | Notariusz |
| Elastyczność | Wysoka | Średnia |
| Koszt założenia | ~2000 PLN | ~2500 PLN |

Gra rekomenduje formę na podstawie Twojej sytuacji.

### Etap 6: Zabezpieczenia prawne

Konfigurujesz klauzule umowy wspólników:

**Vesting** (nabywanie udziałów w czasie)
- Okres vestingu (typowo: 48 miesięcy)
- Cliff (okres próbny, typowo: 12 miesięcy)
- Procent po cliffie (typowo: 25%)

**Klauzule ochronne:**
- Tag-along (prawo przyłączenia do sprzedaży)
- Drag-along (prawo pociągnięcia do sprzedaży)
- Good/bad leaver (warunki odejścia)
- IP protection (ochrona własności intelektualnej)
- Non-compete (zakaz konkurencji)
- NDA (klauzula poufności)

### Etap 7: Cele biznesowe

Definiujesz cele na 6 i 12 miesięcy:
- MRR (przychód miesięczny)
- Liczba klientów

Gra będzie śledzić postępy.

### Etap 8: Ustawienia symulacji

- **Trudność**: łatwa / normalna / trudna
- **Zdarzenia losowe**: tak / nie
- **Szczegółowe objaśnienia**: tak / nie

## Rozgrywka

### Podstawowe komendy

| Komenda | Opis |
|---------|------|
| `status` | Aktualny stan firmy |
| `miesiac` | Przejdź do następnego miesiąca |
| `ryzyko` | Analiza ryzyka firmy |
| `finanse` | Szczegóły finansowe |
| `equity` | Cap table - tabela udziałów |
| `umowa` | Status umowy wspólników |
| `zapisz` | Zapisz stan gry |
| `wczytaj` | Wczytaj zapisaną grę |
| `eksport` | Eksportuj do YAML |

### Komendy edukacyjne

| Komenda | Temat |
|---------|-------|
| `nauka formy` | Porównanie PSA vs Sp. z o.o. |
| `nauka vesting` | Jak działa vesting |
| `nauka leaver` | Good/bad leaver |
| `nauka tagdrag` | Tag-along / drag-along |
| `nauka ip` | Ochrona własności intelektualnej |
| `nauka partner` | Weryfikacja partnera |
| `nauka mvp` | Wycena MVP |
| `nauka equity` | Podział udziałów |
| `slownik` | Słownik pojęć |

### Symulacja miesięczna

Komenda `miesiac` przesuwa czas o miesiąc. W każdym miesiącu:

1. **Wzrost organiczny**
   - Klienci rosną o 5-15%
   - MRR rośnie proporcjonalnie

2. **Spalanie gotówki**
   - Cash = Cash - burn_rate + MRR

3. **Vesting**
   - Postęp vestingu dla wszystkich founderów

4. **Zdarzenia losowe** (jeśli włączone)
   - Szansa na pozytywne/negatywne wydarzenia
   - Decyzje do podjęcia

5. **Aktualizacja wyceny**
   - Valuation = 5 × ARR

### Zdarzenia losowe

**Pozytywne (zwiększają szanse na sukces):**
- 🚀 Viral marketing - nagły wzrost użytkowników
- 🤝 Strategiczny partner - nowe możliwości
- 💼 Enterprise klient - duży kontrakt
- 🏆 Nagroda branżowa - rozpoznawalność

**Negatywne (wymagają reakcji):**
- 💰 Konkurent otrzymał funding
- 👤 Kluczowy pracownik odchodzi
- ⚔️ Konflikt między founderami
- 🔧 MVP nie działa jak trzeba
- 💸 Problem z płynnością
- 🔒 Naruszenie danych
- 📋 Zmiany regulacyjne

### Podejmowanie decyzji

Przy niektórych zdarzeniach musisz podjąć decyzję:

```
DECYZJA: Kluczowy pracownik chce odejść do konkurencji

1. Dopasuj wynagrodzenie (+15% do kosztów)
2. Zaproponuj equity (z puli ESOP)
3. Pozwól odejść (ryzyko utraty wiedzy)

Wybór (1/2/3): 
```

Każda opcja ma konsekwencje finansowe i strategiczne.

## Analiza ryzyka

Komenda `ryzyko` pokazuje:
- **Wynik ryzyka** (0-100): im wyższy, tym gorzej
- **Krytyczne zagrożenia**
- **Rekomendacje**

Czynniki ryzyka:
- Runway < 3 miesięcy = krytyczny
- Brak vestingu = +5 punktów
- Niezweryfikowany partner = +10 punktów
- Brak product-market fit po 6 miesiącach = +15 punktów

## Warunki zakończenia

### Sukces 🏆
- Osiągnięcie celów MRR i klientów
- Dodatni runway
- Wszystkie zobowiązania prawne spełnione

### Porażka 💀
- Gotówka ≤ 0
- Upadłość firmy
- Konflikt prowadzący do rozpadu spółki

## Eksport konfiguracji

Komenda `eksport plik.yaml` zapisuje wszystkie parametry gry:

```yaml
player:
  name: Jan
  role: technical
mvp:
  value: 70000
partner:
  name: Anna
  capital: 20000
equity:
  player: 55
  partner: 35
  esop: 10
# ... więcej parametrów
```

Plik można:
- Pokazać prawnikowi jako podstawę umowy
- Przedyskutować z partnerem
- Użyć jako checklistę przy zakładaniu firmy

## Wskazówki

### Dla początkujących
1. Zacznij od trudności "łatwa"
2. Włącz szczegółowe objaśnienia
3. Użyj komend `nauka` przed każdą decyzją
4. Sprawdzaj `ryzyko` co 2-3 miesiące

### Dla zaawansowanych
1. Trudność "trudna" ma więcej zdarzeń negatywnych
2. Eksperymentuj z różnymi podziałami equity
3. Porównuj scenariusze z różnymi formami prawnymi
4. Analizuj, jakie zabezpieczenia są kluczowe

## Zapisywanie postępów

```bash
(biznes) zapisz moja_gra
Zapisano: ~/.biznes_saves/moja_gra.yaml

(biznes) wczytaj moja_gra
Wczytano grę z miesiąca 6
```

Gra automatycznie zapisuje się po każdej ważnej decyzji.
