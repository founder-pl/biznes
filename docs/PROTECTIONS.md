# 🛡️ Zabezpieczenia prawne w startupie

## Umowa wspólników (SHA)

Shareholders Agreement to dokument regulujący relacje między wspólnikami. Powinien zawierać wszystkie poniższe elementy.

## Vesting

### Czym jest?

Mechanizm stopniowego nabywania udziałów w czasie, który:
- Chroni przed odejściem wspólnika z pełnym pakietem
- Motywuje do długoterminowej pracy
- Daje bezpieczeństwo pozostałym wspólnikom

### Standard rynkowy

```
Okres:      48 miesięcy (4 lata)
Cliff:      12 miesięcy
Po cliffie: 25% vestuje od razu
Potem:      ~2% miesięcznie (równomiernie)
```

### Konfiguracja w grze

Gra pozwala dostosować:
- Długość vestingu (24-60 miesięcy)
- Długość cliffu (0-18 miesięcy)
- Procent po cliffie (0-50%)

### Wzór

```
Vested = (Miesiące_po_cliff / Miesiące_vesting) × Procent_total
```

## Good/Bad Leaver

### Good leaver - kiedy?

1. **Śmierć lub trwała niezdolność** - Najczystszy przypadek. Udziały mogą przejść na spadkobierców.

2. **Zwolnienie bez podania przyczyny** - Spółka decyduje, że nie chce już wspólnika, mimo że nie zawinił.

3. **Poważna choroba** - Trwająca > 6 miesięcy, uniemożliwiająca pracę.

4. **Istotna zmiana warunków** - Np. przeniesienie siedziby o 100+ km bez zgody.

5. **Przejście na emeryturę** - Po osiągnięciu wieku emerytalnego.

### Good leaver - konsekwencje

✅ Zatrzymuje wszystkie zvested udziały
❌ Niewested udziały przepadają
⚖️ Odkup po fair market value (FMV)

### Bad leaver - kiedy?

1. **Rezygnacja w okresie cliff** - Odejście przed ukończeniem próbnego okresu.

2. **Ciężkie naruszenie umowy** - Np. działanie na szkodę spółki, kradzież.

3. **Konkurencja** - Założenie lub praca dla konkurenta w okresie non-compete.

4. **Skazanie za przestępstwo** - Szczególnie przestępstwa gospodarcze.

5. **Oszustwo wobec spółki** - Fałszowanie dokumentów, malwersacje.

### Bad leaver - konsekwencje

❌ Traci WSZYSTKIE udziały (nawet zvested)
💰 Lub: przymusowy odkup za wartość nominalną (np. 1 PLN/udział)
⚠️ Może zachować część przy łagodniejszych zapisach

### Definiowanie w umowie

```
WAŻNE: Umowa MUSI precyzyjnie definiować wszystkie przypadki.
Niejasne zapisy = spory sądowe.
```

Przykład dobrego zapisu:
> "Za bad leaver uznaje się wspólnika, który: (a) rozwiązuje stosunek pracy/B2B jednostronnie w okresie pierwszych 24 miesięcy..."

## Tag-along (prawo przyłączenia)

### Czym jest?

Prawo mniejszościowego wspólnika do sprzedaży swoich udziałów na tych samych warunkach, gdy większościowy sprzedaje swoje.

### Przykład

```
Sytuacja:
- Founder A: 55%
- Founder B: 35%
- ESOP: 10%

Founder A chce sprzedać 55% za 1 000 000 PLN.
Kupiec oferuje 18 182 PLN za 1% (proporcjonalnie).

Z tag-along:
Founder B może przyłączyć się i sprzedać swoje 35% za 636 370 PLN.

Bez tag-along:
Founder B zostaje z 35% w firmie kontrolowanej przez nowego właściciela.
```

### Dlaczego ważne?

- Chroni mniejszościowego wspólnika przed "uwięzieniem"
- Zapewnia równe traktowanie przy exit
- Standard w profesjonalnych umowach

### Konfiguracja

✅ **Zalecane:** Włączone dla wszystkich wspólników
⚠️ **Uwaga:** Może utrudnić częściową sprzedaż

## Drag-along (prawo pociągnięcia)

### Czym jest?

Prawo większościowego wspólnika do zmuszenia mniejszościowego do sprzedaży przy exit.

### Przykład

```
Sytuacja:
- Founder A: 55%
- Founder B: 35%

Kupiec chce kupić 100% firmy za 2 000 000 PLN.

Z drag-along:
Founder A (mając > 50%) może zmusić Founder B do sprzedaży.
Obaj dostają proporcjonalną część (A: 1.1M, B: 0.7M).

Bez drag-along:
Founder B może zablokować transakcję, żądając więcej lub odmawiając.
```

### Dlaczego ważne?

- Umożliwia pełny exit bez blokady
- Kupcy zwykle chcą 100%
- Zapobiega "szantażowi" mniejszościowego wspólnika

### Progi aktywacji

- Typowy próg: 50% + 1 głos
- Czasem: 66% lub 75% (superwięskzość)
- Warto negocjować minimalną cenę

## Non-compete (zakaz konkurencji)

### Czym jest?

Klauzula zakazująca pracy dla konkurencji lub zakładania konkurencyjnej firmy.

### Limity prawne w Polsce

- **Maksymalny czas:** 24 miesiące
- **Geograficzny zakres:** musi być uzasadniony
- **Wynagrodzenie:** przy UoP wymagane (min. 25% wynagrodzenia)

### Konfiguracja

```
Okres:          6-24 miesięcy
Zakres:         Definiowana branża/działalność
Teren:          Polska / EU / globalnie
Kary:           50 000 - 200 000 PLN
```

### Egzekwowanie

⚠️ **Ważne:** Trudne do wyegzekwowania przy B2B
✅ Łatwiejsze przy UoP z odpowiednim wynagrodzeniem
📋 Wymagany precyzyjny opis zakazanej działalności

## NDA (klauzula poufności)

### Czym jest?

Umowa o zachowaniu poufności informacji biznesowych.

### Co obejmuje?

- Kod źródłowy i architektura
- Lista klientów
- Warunki umów
- Plany biznesowe
- Know-how i procesy

### Typowe kary

```
Naruszenie NDA:      30 000 - 50 000 PLN
Za każdy przypadek:  Dodatkowa kara
Górny limit:         Często bez limitu
```

### Czas obowiązywania

- **W trakcie współpracy:** Zawsze
- **Po zakończeniu:** 2-5 lat (typowo)
- **Trade secrets:** Bezterminowo

## IP Protection (własność intelektualna)

### Background IP vs Foreground IP

**Background IP** - własność intelektualna powstała PRZED współpracą:
- Pozostaje własnością twórcy
- Licencjonowana do spółki (nie przenoszona!)
- Chroni twórcę przy odejściu

**Foreground IP** - własność intelektualna powstała W TRAKCIE współpracy:
- Automatycznie własność spółki
- Transfer w momencie powstania

### IP Assignment (cesja)

Dokument przenoszący prawa autorskie do kodu/produktu na spółkę.

```
WYMAGANE:
✅ Pisemna forma
✅ Wynagrodzenie (nawet symboliczne)
✅ Specyfikacja co jest przenoszone
```

### Conditional License (licencja warunkowa)

Mechanizm ochrony twórcy MVP:

```
Warunki licencji:
1. Partner wnosi kapitał (20 000 PLN) w ciągu 30 dni
2. Spółka zostaje założona w ciągu 60 dni
3. Podpisana umowa wspólników z vestingiem

Jeśli warunki NIE są spełnione:
→ Licencja wygasa
→ MVP wraca do twórcy
```

Podstawa prawna: Art. 89-94 Kodeksu Cywilnego (warunek zawieszający).

## Deadlock Resolution (rozwiązywanie impasów)

### Czym jest?

Mechanizm rozstrzygania patowych sytuacji przy 50/50 lub gdy wspólnicy nie mogą dojść do porozumienia.

### Metody

**1. Russian Roulette (Shotgun clause)**
Jeden wspólnik proponuje cenę. Drugi musi albo kupić, albo sprzedać po tej cenie.

**2. Texas Shootout**
Obaj wspólnicy składają oferty w zamkniętych kopertach. Wyższa wygrywa.

**3. Mediacja**
Obowiązkowa próba mediacji przed postępowaniem sądowym.

**4. Arbitraż**
Rozstrzygnięcie przez arbitra (szybsze niż sąd).

## Checklist umowy wspólników

### Obowiązkowe

- [ ] Vesting (okres, cliff, procenty)
- [ ] Good/bad leaver (definicje, konsekwencje)
- [ ] IP assignment (background vs foreground)
- [ ] Non-compete (czas, zakres, kary)
- [ ] NDA (czas, zakres, kary)

### Zalecane

- [ ] Tag-along
- [ ] Drag-along
- [ ] Deadlock resolution
- [ ] Acceleration przy exit
- [ ] Prawo pierwokupu

### Opcjonalne

- [ ] Liquidation preference
- [ ] Anti-dilution
- [ ] Board seats
- [ ] Information rights

## Koszty prawne

| Dokument | Koszt orientacyjny |
|----------|-------------------|
| Umowa wspólników (SHA) | 3 000 - 8 000 PLN |
| IP assignment | 1 000 - 2 000 PLN |
| NDA | 500 - 1 500 PLN |
| Pełny pakiet startup | 5 000 - 15 000 PLN |

## Eksport z gry

Komenda `eksport config.yaml` generuje plik z wszystkimi ustalonymi zabezpieczeniami, który można:
- Pokazać prawnikowi jako brief
- Przedyskutować z partnerem
- Użyć jako checklistę
