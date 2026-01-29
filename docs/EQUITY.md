# 💰 Podział equity między founderami

## Podstawowe zasady

### Zasada 1: Nigdy nie dziel 50/50 bez przemyślenia

Podział 50/50 wydaje się "sprawiedliwy", ale:
- Nie odzwierciedla różnych wkładów
- Prowadzi do impasów decyzyjnych (deadlock)
- Ignoruje przyszłe zaangażowanie

### Zasada 2: Vesting chroni wszystkich

Bez vestingu:
- Partner może odejść z 50% firmy po miesiącu
- Nie ma motywacji do długoterminowej pracy
- Inwestorzy nie zainwestują

Z vestingiem:
- Udziały nabywane w czasie (4 lata)
- Cliff chroni pierwszy rok
- Sprawiedliwe dla tych, co zostają

### Zasada 3: Umowa pisemna ZAWSZE

Ustne ustalenia nie mają wartości. Każdy podział musi być:
- Zapisany w umowie spółki lub SHA
- Podpisany przez wszystkich wspólników
- Zawierający warunki vestingu i leaver

## Czynniki wpływające na podział

### 1. MVP / Produkt (15-30%)

Jeśli jeden z founderów wnosi gotowy produkt:

| Stan produktu | Wartość dodana |
|---------------|----------------|
| Pomysł | 0% |
| POC (proof of concept) | 5-10% |
| MVP z pierwszymi userami | 15-20% |
| Produkt z płacącymi klientami | 20-30% |

### 2. Kapitał (10-25%)

Wniesione pieniądze mają wartość, szczególnie na start:

| Kwota (PLN) | Wartość dodana |
|-------------|----------------|
| 5 000 - 20 000 | 5-10% |
| 20 000 - 50 000 | 10-15% |
| 50 000 - 100 000 | 15-20% |
| > 100 000 | 20-25% |

### 3. Doświadczenie branżowe (5-15%)

| Doświadczenie | Wartość dodana |
|---------------|----------------|
| 0-2 lata | 0-5% |
| 3-5 lat | 5-10% |
| 6-10 lat | 10-12% |
| > 10 lat / ekspert | 12-15% |

### 4. Klienci / Kontakty (5-15%)

| Poziom | Wartość dodana |
|--------|----------------|
| Brak | 0% |
| Potencjalni klienci (LOI) | 5% |
| Pierwsi płacący klienci | 10% |
| Duży klient enterprise | 15% |

### 5. Czas i zaangażowanie (10-20%)

| Zaangażowanie | Wartość dodana |
|---------------|----------------|
| Part-time (< 20h/tyg) | 5% |
| Full-time bez pensji | 15% |
| Full-time z minimalną pensją | 10% |

## Scenariusze z gry Biznes

### Scenariusz 1: Programista z MVP

**Sytuacja:**
- Ty (technical): 400h pracy nad MVP, wartość 60 000 PLN
- Partner (business): 20 000 PLN kapitału, 5 lat doświadczenia, 3 klientów

**Rekomendowany podział:**
- Technical: 55-60%
- Business: 30-35%
- ESOP: 10%

**Dlaczego?**
- MVP to namacalna wartość (nie tylko pomysł)
- Partner wnosi kapitał, ale bez produktu jest bezwartościowy
- Doświadczenie i klienci partnera są wartościowe, ale wtórne

### Scenariusz 2: Równy start

**Sytuacja:**
- Obaj founderzy startują od zera
- Każdy wnosi 10 000 PLN
- Obaj full-time

**Rekomendowany podział:**
- Founder A: 45%
- Founder B: 45%
- ESOP: 10%

**Dlaczego?**
- Równe wkłady = równy podział
- ESOP od początku (łatwiej dać przed rundą)

### Scenariusz 3: Sweat equity

**Sytuacja:**
- Ty (technical): brak kapitału, tylko praca
- Partner: 100 000 PLN kapitału, kontakty enterprise

**Rekomendowany podział:**
- Technical: 35-40% (vesting 4 lata!)
- Business: 50-55%
- ESOP: 10%

**Dlaczego?**
- Kapitał i kontakty są natychmiast wartościowe
- Twoja praca ma wartość, ale "zamrożoną" w vestingu
- Z czasem wyrównasz przez vesting

## Pula ESOP

### Co to jest?

Employee Stock Option Pool - udziały zarezerwowane dla przyszłych kluczowych pracowników.

### Ile zarezerwować?

| Faza | Zalecany ESOP |
|------|---------------|
| Pre-seed | 5-10% |
| Seed | 10-15% |
| Series A | 15-20% |

### Kiedy utworzyć?

**ZAWSZE przed pierwszą rundą inwestycyjną!**

Dlaczego?
- ESOP tworzony przed rundą = rozwodnienie founderów
- ESOP tworzony po rundzie = rozwodnienie inwestorów (nie zgodzą się)

**Przykład:**
```
Przed rundą:
- Founder A: 55%
- Founder B: 35%
- ESOP: 10%

Inwestor wchodzi za 20%:
- Founder A: 44% (55% × 0.8)
- Founder B: 28% (35% × 0.8)
- ESOP: 8% (10% × 0.8)
- Inwestor: 20%
```

## Vesting - szczegóły

### Standard rynkowy

- **Okres:** 48 miesięcy (4 lata)
- **Cliff:** 12 miesięcy
- **Procent po cliffie:** 25%
- **Potem:** miesięcznie (~2% miesięcznie)

### Przykład liczbowy

Founder ma 60% equity z 4-letnim vestingiem:

| Miesiąc | Wydarzenie | Vested | Total vested |
|---------|------------|--------|--------------|
| 0-11 | Cliff | 0% | 0% |
| 12 | Cliff kończy się | 15% | 15% |
| 13 | + miesięczny vesting | 1.25% | 16.25% |
| 24 | Rok 2 | - | 30% |
| 36 | Rok 3 | - | 45% |
| 48 | Rok 4 | - | 60% |

### Acceleration

Przyspieszenie vestingu przy szczególnych wydarzeniach:

**Single trigger:** Pełny vesting przy przejęciu firmy.

**Double trigger:** Pełny vesting gdy:
1. Firma zostanie przejęta ORAZ
2. Founder zostanie zwolniony w ciągu 12 miesięcy

Rekomendacja: Double trigger (bardziej fair).

## Good/Bad leaver

### Good leaver

Odchodzisz z uzasadnionych powodów:
- Śmierć lub trwała niezdolność do pracy
- Zwolnienie bez podania przyczyny
- Poważna choroba
- Istotna zmiana warunków (np. przeniesienie siedziby o 100+ km)

**Konsekwencje:**
- Zatrzymujesz wszystkie zvested udziały
- Niewested przepadają

### Bad leaver

Odchodzisz z własnej winy:
- Rezygnacja bez uzasadnienia w okresie cliff
- Ciężkie naruszenie umowy
- Działanie na szkodę spółki
- Skazanie za przestępstwo
- Konkurencja w okresie non-compete

**Konsekwencje:**
- Tracisz WSZYSTKIE udziały (nawet zvested)
- Lub: odkupione za wartość nominalną (1 PLN/udział)

### Szare strefy

Umowa powinna precyzyjnie definiować, co jest good/bad leaver. Niejasności prowadzą do sporów.

## Negocjacje

### Jak negocjować?

1. **Przygotuj dane** - wycena MVP, wartość kapitału, benchmarki rynkowe
2. **Słuchaj** - zrozum perspektywę partnera
3. **Szukaj win-win** - nie walcz o każdy procent
4. **Dokumentuj** - ustalenia na piśmie od razu

### Red flags w negocjacjach

🚩 "Ustalmy equity później, jak zobaczymy kto ile robi"
🚩 "Zaufaj mi, nie potrzebujemy umowy"
🚩 "Ty masz tylko pomysł, ja mam kapitał = 50/50"
🚩 "Vesting? Nie potrzebujemy, ufamy sobie"
🚩 Partner odmawia weryfikacji (KRS, rejestry)

### Kiedy odejść od stołu

- Partner nie chce żadnej umowy pisemnej
- Propozycja jest rażąco nieuczciwa
- Partner ma historię konfliktów/upadłości
- Brak transparentności finansowej

## Narzędzia

### Kalkulator equity w grze Biznes

Gra automatycznie oblicza rekomendowany podział na podstawie:
- Wartości MVP (godziny × stawka)
- Kapitału partnera
- Doświadczenia i kontaktów
- Planowanego zaangażowania

### Eksport do prawnika

Komenda `eksport` generuje YAML z wszystkimi parametrami, który można pokazać prawnikowi jako podstawę umowy wspólników.
