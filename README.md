# Bank Scrapers

Skrypty do pobierania kursów walut z różnych banków

## Po co to wszystko?

Do przeliczania kredytów frankowych. Obecnie toczy się wiele procesów kredytobiorców przeciwko bankom.
Kredytobiorcy twierdzą, że zostali oszukani przez banki, banki z kolei uważają, że działały zgodnie z prawem.
W sądach powoływani są biegli i to oni dokonują wszelkich przeliczeń. Do tego jednak potrzebują właśnie tych danych.

Problem polegam na tym, że mało który bank udostępnia publiczne API, przez które każdy chętny mógłby pobrać interesujące dane.
Dlatego dane trzeba pobierać bezpośrednio z serwisów webowych prezentujących kursy walut w poszczególnych dniach.
Ręczne pobieranie nie wchodzi w grę - zajęłoby ogromną ilość czasu (kilkanaście tysięcy notowań w każdym z banków). Na szczęście z pomocą przychodzi automatyzacja.

## Forma

Ustalenie konkretnego miejsca, z którego należy pobrać dane, odbywało się za pomocą przeglądarki oraz narzędzi deweloperskich poprzez analizę parametrów, żądań i odpowiedzi na nie.

Do całego zadania były dwa podejścia, stąd końcówka `-nowe` w niektórych folderach.
Skrypt ewoluował z każdą iteracją i przy każdym banku wyglądał nieco inaczej.
Ostatnie wersje to te przygotowane pod banki [Millenium](./Millenium-nowe/millenium.py) oraz [BPH](./BPH-nowe/bph-1-bph.py).
Folder [common](./common/) zawiera skrypty służące do obróbki wyników, wspólne dla wszystkich banków.

## Efekty

Dane, które zostały pobrane i obrobione są idealne, tzn. zawierają wszystkie daty od samego początku prowadzenia notowań, czasami nawet te, które nie są widoczne na stronie internetowej.
Zaznaczone są również brakujące notowania.
Efekt prac znajduje się w folderze [Kursy](./Kursy_2023-01-20/).

Oczywiście mam świadomość, że kod jest _nie jest zbyt ładny_ i dałoby się to zrobić lepiej, ale tutaj liczyło się osiągnięcie celu.

## Problemy

Dużo uwagi zostało poświęconej wyłapywaniu błędów, w szczególności brakujących rekordów - stąd obecność plików `-FAILS.txt`.
Poza tym natrafiłem na szereg różnych problemów, pustych rekordów od zwracania dwóch różnych odpowiedzi na dokładnie to samo żądanie GET.

Najczęstsze problemy:

- zwracanie notowań z inną datą niż żądana (sic!)
- różne odpowiedzi na to samo żądanie GET
- trudność w odróżnieniu braku danych od przekroczenia limitu pobierania
- ograniczanie prędkości pobierania i liczby jednoczesnych połączeń
- błędy w migracji danych przy przejmowaniu banków
- niejednolita struktura danych w obrębie tej samej tabeli
- zmiana struktury rekordu w czasie
- wymaganie tokenów autoryzacyjnych
- używanie metody POST zamiast GET
- mnóstwo przypadków brzegowych i wyjątków
- odpowiedzi w formacie html zamiast w json
- brak ciągłości numerów notowań
- dziwne sposoby zaznaczania braków notowań
- problematyczne wyciąganie godzin notowań w poszczególnych dniach
- puste notowania
- notowania w święta
