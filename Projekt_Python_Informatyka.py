import sys
# Import bibliotek graficznych (okna, przyciski, rysowanie)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTabWidget, 
                             QTextEdit, QSpinBox)
from PyQt6.QtCore import QTimer, Qt, QRect
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath

# ==========================================
# CZĘŚĆ 1: MODEL DANYCH (LOGIKA OBIEKTOWA)
# ==========================================

class Zbiornik:
    """Klasa reprezentująca pojedynczy zbiornik w systemie."""
    def __init__(self, x, y, w, h, max_poziom, nazwa):
        self.rect = QRect(x, y, w, h) # Wymiary i pozycja do rysowania
        self.poziom = 0.0             # Aktualna ilość cieczy (L)
        self.max_poziom = max_poziom  # Pojemność maksymalna (L)
        self.temp = 20.0              # Temperatura cieczy (stopnie C)
        self.nazwa = nazwa            # Etykieta (np. "Z1")

    def dodaj_ciecz(self, ilosc):
        """Dodaje ciecz, pilnując by nie przelać zbiornika."""
        if self.poziom + ilosc <= self.max_poziom:
            self.poziom += ilosc
            return True
        return False

    def pobierz_ciecz(self, ilosc):
        """Pobiera ciecz, pilnując by nie zejść poniżej zera."""
        if self.poziom > 0:
            ilosc_faktyczna = min(self.poziom, ilosc) # Nie pobieraj więcej niż jest
            self.poziom -= ilosc_faktyczna
            return ilosc_faktyczna
        return 0

class Urzadzenie:
    """Klasa dla urządzeń wykonawczych (Pompa, Grzałka)."""
    def __init__(self, x, y, nazwa):
        self.x = x
        self.y = y
        self.nazwa = nazwa
        self.aktywne = False # Stan urządzenia: True=Włączone, False=Wyłączone

class Rura:
    """Klasa przechowująca współrzędne rur do narysowania."""
    def __init__(self, punkty):
        self.punkty = punkty # Lista punktów [(x1,y1), (x2,y2)...]

# ==========================================
# CZĘŚĆ 2: WIDOK I SYMULACJA (SCADA)
# ==========================================

class EkranWizualizacji(QWidget):
    """Główny ekran, na którym rysowany jest schemat i odbywa się symulacja."""
    
    def __init__(self, raport_callback):
        super().__init__()
        self.raport_callback = raport_callback # Funkcja do wysyłania logów tekstowych
        
        # --- KONFIGURACJA ZBIORNIKÓW ---
        # Definicja 4 zbiorników w odpowiednich miejscach ekranu
        self.zbiorniki = [
            Zbiornik(50, 50, 80, 120, 100, "Z1 (Surowiec)"),
            Zbiornik(250, 50, 80, 120, 100, "Z2 (Bufor)"),
            Zbiornik(50, 350, 80, 120, 100, "Z3 (Grzanie)"),
            Zbiornik(250, 350, 80, 120, 100, "Z4 (Produkt)")
        ]
        self.zbiorniki[0].poziom = 90.0 # Z1 napełniony na start
        
        # --- KONFIGURACJA URZĄDZEŃ ---
        self.pompa = Urzadzenie(145, 185, "Pompa P1") 
        self.grzalka = Urzadzenie(65, 480, "Grzałka G1") 

        # --- KONFIGURACJA RUR (Połączenia między zbiornikami) ---
        self.rury = [
            # Rura 1: Z1 -> Z2 (Przez pompę)
            Rura([
                (90, 170), (90, 200), (230, 200), (230, 30), (290, 30), (290, 60)
            ]),
            # Rura 2: Z2 -> Z3 (Grawitacyjna - środek ekranu)
            Rura([
                (290, 170), (290, 260), (90, 260), (90, 350)
            ]),
            # Rura 3: Z3 -> Z4 (Zrzut produktu)
            Rura([
                (90, 470), (90, 510), (230, 510), (230, 330), (290, 330), (290, 360)
            ])
        ]

        # --- ZEGAR SYMULACJI ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.symuluj_proces) # Co cykl wywołaj symuluj_proces()
        
        # Zmienne sterujące procesem
        self.cykl = 0
        self.szybkosc_pompy = 0
        self.temp_cel = 0
        self.zawor_z3_otwarty = False

        # Ustawienie czcionki dla napisów na schemacie
        self.font_opis = QFont("Arial", 10, QFont.Weight.Bold)

    def start_proces(self, szybkosc_pompy, temp_cel):
        """Uruchamia symulację po kliknięciu przycisku START."""
        self.szybkosc_pompy = szybkosc_pompy
        self.temp_cel = temp_cel
        self.zawor_z3_otwarty = False
        # Logowanie startu
        self.raport_callback(f"START: Cel={temp_cel}°C, Pompa={szybkosc_pompy}")
        self.timer.start(100) # Uruchomienie zegara co 100ms (0.1s)

    def symuluj_proces(self):
        """Główna pętla fizyki - oblicza przepływy i temperatury."""
        z1, z2, z3, z4 = self.zbiorniki
        
        # --- KROK 1: POMPOWANIE (Z1 -> Z2) ---
        # Pompa działa, jeśli w Z1 jest ciecz, a Z2 nie jest pełny
        if z1.poziom > 0 and z2.poziom < z2.max_poziom:
            self.pompa.aktywne = True
            # Przepływ zależy od ustawionej mocy pompy
            flow = self.szybkosc_pompy * 0.15
            pobrane = z1.pobierz_ciecz(flow)
            z2.dodaj_ciecz(pobrane)
        else:
            self.pompa.aktywne = False

        # --- KROK 2: GRAWITACJA (Z2 -> Z3) ---
        # Swobodny spływ z bufora do zbiornika grzewczego
        if z2.poziom > 0 and z3.poziom < z3.max_poziom:
            flow_grawitacja = 0.4 # Stała, mniejsza prędkość grawitacji
            pobrane = z2.pobierz_ciecz(flow_grawitacja)
            z3.dodaj_ciecz(pobrane)

        # --- KROK 3: GRZANIE (Z3) ---
        # Grzałka włącza się, gdy jest ciecz (>1L) i temp. jest za niska
        if z3.poziom > 1:
            self.grzalka.aktywne = True
            if z3.temp < self.temp_cel:
                z3.temp += 0.4 # Wzrost temperatury
        else:
            self.grzalka.aktywne = False
            # Naturalne stygnięcie, gdy grzałka nie działa
            if z3.temp > 20: z3.temp -= 0.05

        # --- KROK 4: ZRZUT PRODUKTU (Z3 -> Z4) ---
        # Otwarcie zaworu, gdy osiągnięto temperaturę docelową
        if z3.temp >= self.temp_cel:
            self.zawor_z3_otwarty = True
        
        # Jeśli zawór otwarty -> przelewamy do Z4
        if self.zawor_z3_otwarty and z3.poziom > 0:
            flow = 0.9 # Szybki zrzut
            pobrane = z3.pobierz_ciecz(flow)
            z4.dodaj_ciecz(pobrane)
            
            # Obliczenie średniej temperatury w Z4 po dolaniu gorącej cieczy
            if z4.poziom > 0:
                z4.temp = (z4.temp * (z4.poziom - pobrane) + z3.temp * pobrane) / z4.poziom
        
        # Zamknięcie zaworu dopiero gdy Z3 będzie pusty
        if z3.poziom <= 0:
            self.zawor_z3_otwarty = False

        # --- AKTUALIZACJA LOGÓW I EKRANU ---
        self.cykl += 1
        if self.cykl % 50 == 0: # Co 50 cykli wpis do logu
            self.raport_callback(f"STAN: Z3 Temp={z3.temp:.1f}°C, Z4 Poziom={z4.poziom:.1f}L")
        
        self.update() # Wymuszenie odrysowania ekranu (wywołuje paintEvent)

    def rysuj_tekst_z_obwodka(self, painter, x, y, tekst, kolor_tekstu=Qt.GlobalColor.white):
        """Metoda pomocnicza do rysowania czytelnych napisów z czarną obwódką."""
        path = QPainterPath()
        path.addText(x, y, self.font_opis, tekst)
        
        # 1. Rysujemy czarną, grubą obwódkę
        painter.setPen(QPen(Qt.GlobalColor.black, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush) 
        painter.drawPath(path)
        
        # 2. Rysujemy kolorowe wypełnienie tekstu na wierzchu
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(kolor_tekstu))
        painter.drawPath(path)

    def paintEvent(self, event):
        """Funkcja rysująca wszystko na ekranie - wywoływana automatycznie."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing) # Wygładzanie krawędzi

        # 1. Rysowanie Rur (Szare linie)
        p.setPen(QPen(QColor(100, 100, 100), 8))
        for rura in self.rury:
            for i in range(len(rura.punkty) - 1):
                p1, p2 = rura.punkty[i], rura.punkty[i+1]
                p.drawLine(p1[0], p1[1], p2[0], p2[1])

        # 2. Rysowanie Zbiorników
        for z in self.zbiorniki:
            # Obrys zbiornika
            p.setPen(QPen(Qt.GlobalColor.black, 3))
            p.setBrush(QBrush(Qt.GlobalColor.white))
            p.drawRect(z.rect)
            
            # Wypełnienie cieczą
            h = int((z.poziom / z.max_poziom) * z.rect.height()) # Wysokość słupka cieczy
            
            # Obliczanie koloru (Interpolacja: Zimny=Niebieski, Gorący=Czerwony)
            ratio = max(0, min(1, (z.temp - 20) / 80))
            r_val = int(255 * ratio)
            b_val = int(255 * (1 - ratio))
            
            p.setBrush(QBrush(QColor(r_val, 0, b_val)))
            # Rysowanie prostokąta cieczy (od dołu zbiornika)
            p.drawRect(z.rect.x(), z.rect.y() + z.rect.height() - h, z.rect.width(), h)
            
            # Podpisy zbiorników (z obwódką)
            self.rysuj_tekst_z_obwodka(p, z.rect.x(), z.rect.y() - 25, z.nazwa)
            self.rysuj_tekst_z_obwodka(p, z.rect.center().x() - 20, z.rect.center().y(), f"{z.poziom:.1f}L")
            
            # Wyświetlanie temperatury tylko na istotnych zbiornikach (Z3, Z4)
            if "Z3" in z.nazwa or ("Z4" in z.nazwa and z.poziom > 0):
                 kolor = QColor("#ff5555") if z.temp > 40 else QColor("white")
                 self.rysuj_tekst_z_obwodka(p, z.rect.center().x() - 20, z.rect.center().y() + 20, 
                                            f"{z.temp:.0f}°C", kolor)

        # 3. Rysowanie Pompy
        # Kolor: Zielony jak aktywna, Czerwony jak stoi
        p.setBrush(QBrush(Qt.GlobalColor.green if self.pompa.aktywne else Qt.GlobalColor.red))
        p.setPen(QPen(Qt.GlobalColor.black, 2))
        p.drawEllipse(self.pompa.x, self.pompa.y, 30, 30)
        self.rysuj_tekst_z_obwodka(p, self.pompa.x - 20, self.pompa.y - 10, "P1 (Pompa)")
        
        # 4. Rysowanie Grzałki
        p.setBrush(QBrush(Qt.GlobalColor.red if self.grzalka.aktywne else Qt.GlobalColor.gray))
        p.setPen(QPen(Qt.GlobalColor.black, 1))
        p.drawRect(self.grzalka.x, self.grzalka.y, 50, 15)
        self.rysuj_tekst_z_obwodka(p, self.grzalka.x, self.grzalka.y + 35, "G1 (Grzałka)")

# ==========================================
# CZĘŚĆ 3: GŁÓWNE OKNO APLIKACJI (GUI)
# ==========================================

class ScadaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCADA PRO - Final Design")
        self.resize(1000, 700)
        
        # Stylizacja całego okna (Ciemny motyw)
        self.setStyleSheet("QMainWindow { background-color: #2b2b2b; }")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- GÓRNY PASEK STEROWANIA ---
        ster = QHBoxLayout()
        lbl_style = "color: white; font-weight: bold; font-size: 14px;"
        
        # Kontrolka: Moc Pompy
        lbl_speed = QLabel("Moc Pompy:")
        lbl_speed.setStyleSheet(lbl_style)
        self.speed = QSpinBox()
        self.speed.setRange(1, 10)
        self.speed.setValue(5)
        self.speed.setFixedSize(80, 30)
        
        # Kontrolka: Temperatura Docelowa
        lbl_temp = QLabel("Cel Temp (°C):")
        lbl_temp.setStyleSheet(lbl_style)
        self.temp = QSpinBox()
        self.temp.setRange(20, 90)
        self.temp.setValue(65)
        self.temp.setFixedSize(80, 30)
        
        # Przycisk START
        btn = QPushButton("START PROCESU")
        btn.setFixedSize(150, 40)
        btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; border-radius: 5px;")
        btn.clicked.connect(self.start)
        
        # Dodanie elementów do paska
        ster.addWidget(lbl_speed)
        ster.addWidget(self.speed)
        ster.addSpacing(30)
        ster.addWidget(lbl_temp)
        ster.addWidget(self.temp)
        ster.addSpacing(30)
        ster.addWidget(btn)
        ster.addStretch() # Dopychanie do lewej
        layout.addLayout(ster)

        # --- ZAKŁADKI (WIZUALIZACJA I LOGI) ---
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #444; color: white; padding: 10px; }
            QTabBar::tab:selected { background: #666; font-weight: bold; }
        """)
        
        self.log = QTextEdit()
        self.log.setReadOnly(True) # Logi tylko do odczytu
        self.log.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        
        self.wiz = EkranWizualizacji(self.log.append)
        
        tabs.addTab(self.wiz, "Wizualizacja")
        tabs.addTab(self.log, "Logi Systemowe")
        layout.addWidget(tabs)

    def start(self):
        """Metoda wywoływana przez przycisk START."""
        self.wiz.start_proces(self.speed.value(), self.temp.value())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ScadaApp()
    w.show()
    sys.exit(app.exec())