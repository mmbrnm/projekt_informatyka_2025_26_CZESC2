# projekt_informatyka_2025_26_CZESC2


## Projekt w Python 
Jakub Szwindowski 
199327
EiA ARISS



## Symulator Procesu Przemysłowego SCADA
## O projekcie
Jest to aplikacja desktopowa napisana w języku Python (przy użyciu biblioteki PyQt6), która symuluje działanie rzeczywistego systemu sterowania i wizualizacji (SCADA). Program na żywo odwzorowuje przepływ cieczy, zmiany temperatury oraz pracę urządzeń wykonawczych, pozwalając użytkownikowi na interaktywne sterowanie parametrami procesu.


## Działanie symulacji
Zaimplementowany układ technologiczny składa się z czterech połączonych ze sobą zbiorników, przez które przechodzi surowiec. Proces przebiega następująco:

1. Pobór i buforowanie: Proces rozpoczyna się w zbiorniku z surowcem (Z1). Pompa P1 przetłacza ciecz do zbiornika Z2, który pełni rolę bufora. Jego zadaniem jest ustabilizowanie przepływu między wydajną pompą a dalszą, grawitacyjną częścią instalacji.

2. Proces termiczny: Z bufora ciecz spływa grawitacyjnie do zbiornika grzewczego (Z3). Znajdująca się tam grzałka podnosi temperaturę medium do wartości ustawionej przez operatora. Zmiana temperatury jest wizualizowana poprzez płynną zmianę koloru cieczy (od zimnego niebieskiego do gorącego czerwonego).

3. Wydanie produktu: System automatyki czuwa nad temperaturą. Dopiero gdy ciecz w Z3 osiągnie zadaną wartość, otwiera się zawór spustowy i gotowy produkt trafia do zbiornika końcowego (Z4).

## Cechy programu
Aplikacja nie korzysta z gotowych grafik – cały schemat, rury oraz poziomy cieczy są rysowane dynamicznie w kodzie. Dzięki temu animacje są płynne i precyzyjnie reagują na zmiany parametrów. Użytkownik ma do dyspozycji panel sterowania, w którym może na bieżąco zmieniać wydajność pompy oraz oczekiwaną temperaturę procesu, a także podglądać logi systemowe.

## Uruchomienie
Projekt wymaga zainstalowanej biblioteki PyQt6. Aby uruchomić symulację, należy włączyć plik: "Projekt_Python_Informatyka.py"
