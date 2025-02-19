import sys
import math
from PyQt6.QtCore import QUrl, QTimer, Qt, QDateTime, QPointF
from PyQt6.QtGui import QKeySequence, QPainter, QPolygonF, QColor, QFont
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QGuiApplication

def mouse_global_event():
    print("Mouse activity detected globally")  # Depuração

class OverlayWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hex_size = 400
        self.setFixedSize(self.hex_size, self.hex_size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Permite eventos passarem
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background: transparent;")  # Fundo transparente
        self.pos_x = 100
        self.pos_y = 100
        self.dx = 2
        self.dy = 2

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.update_position)
        self.anim_timer.start(30)

    def update_position(self):
        self.pos_x += self.dx
        self.pos_y += self.dy

        if self.parent():
            parent_width = self.parent().width()
            parent_height = self.parent().height()
        else:
            parent_width, parent_height = 800, 600

        if self.pos_x <= 0 or self.pos_x + self.hex_size >= parent_width:
            self.dx = -self.dx
            self.pos_x = max(0, min(self.pos_x, parent_width - self.hex_size))
        if self.pos_y <= 0 or self.pos_y + self.hex_size >= parent_height:
            self.dy = -self.dy
            self.pos_y = max(0, min(self.pos_y, parent_height - self.hex_size))

        self.move(self.pos_x, self.pos_y)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        radius = self.hex_size / 2
        center_x, center_y = self.hex_size / 2, self.hex_size / 2
        hexagon = QPolygonF()
        for i in range(6):
            angle_deg = 60 * i - 30
            x = center_x + radius * math.cos(math.radians(angle_deg))
            y = center_y + radius * math.sin(math.radians(angle_deg))
            hexagon.append(QPointF(x, y))

        painter.setBrush(QColor("#1976d2"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(hexagon)

        font = QFont("Arial", 25)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor("white"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Olá,\nUtilize o mouse\n para navegar\n em nosso \npainel interativo.")


class FullScreenApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # No construtor
        QGuiApplication.instance().installEventFilter(self)
        self.setWindowTitle("Painel Interativo FCT")
        self.showFullScreen()
        self.setMouseTracking(True)  # Ativar rastreamento do mouse

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        menu = QWidget()
        menu_layout = QHBoxLayout(menu)
        menu_layout.setSpacing(20)
        menu.setFixedHeight(60)

        self.btn_home = QPushButton("Conheca o Campus")
        self.btn_horarios = QPushButton("Horários de Aulas")
        self.btn_fct_pessoas = QPushButton("Conheça a FCT - Pessoas")
        self.btn_fct_extensao = QPushButton("Conheça a FCT - Ações de Extensão")
        for btn in [self.btn_home,self.btn_horarios, self.btn_fct_pessoas, self.btn_fct_extensao]:
            menu_layout.addWidget(btn)

        self.webview = QWebEngineView()
        layout.addWidget(menu)
        layout.addWidget(self.webview)

        self.setStyleSheet("""
            QWidget { background-color: #1a237e; }
            QPushButton {
                background-color: #1976d2; color: white; border: none;
                padding: 10px 20px; font-size: 20px; border-radius: 2px;
            }
            QPushButton:hover { background-color: #2196f3; }
        """)

        self.btn_home.clicked.connect(lambda: self.carregar_url("https://prezi.com/view/MZjulFdzyMstq9zoDLVX/"))
        self.btn_horarios.clicked.connect(lambda: self.carregar_url("https://ti-fct.github.io/horariosFCT/"))
        self.btn_fct_pessoas.clicked.connect(lambda: self.carregar_url("https://app.powerbi.com/view?r=eyJrIjoiNjUzMDMzOWUtNzViNS00NGYyLTk1YTYtMWY5MWE5OGI1YzAzIiwidCI6ImIxY2E3YTgxLWFiZjgtNDJlNS05OGM2LWYyZjJhOTMwYmEzNiJ9"))
        self.btn_fct_extensao.clicked.connect(lambda: self.carregar_url("https://app.powerbi.com/view?r=eyJrIjoiMDcyZWQ2NWMtZTVkMy00YzMyLTkyYjQtNzFmMjQ1MzVjZDcwIiwidCI6ImIxY2E3YTgxLWFiZjgtNDJlNS05OGM2LWYyZjJhOTMwYmEzNiJ9"))

        self.carregar_url("https://prezi.com/view/MZjulFdzyMstq9zoDLVX/")
        self.overlay = OverlayWidget(self)
        self.overlay.hide()  # Inicialmente oculto

        self.lastActivity = QDateTime.currentDateTime()
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.updateOverlayVisibility)
        self.idle_timer.start(1000)  # Verifica a cada segundo

        # Adicionar um filtro de eventos global
        self.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == event.Type.MouseMove:
            print("Mouse moved (event filter)")  # Depuração
            self.lastActivity = QDateTime.currentDateTime()
            if self.overlay.isVisible():
                print("Hiding hexagon (event filter)")  # Depuração
                self.overlay.hide()
        return super().eventFilter(source, event)

    def carregar_url(self, url: str):
        self.webview.load(QUrl(url))

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Close):
            event.ignore()

    # def mouseMoveEvent(self, event):
    #     print("Mouse moved")  # Depuração
    #     self.lastActivity = QDateTime.currentDateTime()
    #     if self.overlay.isVisible():
    #         print("Hiding hexagon")  # Depuração
    #         self.overlay.hide()
    #     super().mouseMoveEvent(event)

    # def updateOverlayVisibility(self):
    #     agora = QDateTime.currentDateTime()
    #     idle_time = self.lastActivity.secsTo(agora)
    #     print(f"Idle time: {idle_time} seconds")  # Depuração

    #     if idle_time >= 300:  # 5 minutos
    #         if not self.overlay.isVisible():
    #             print("Showing hexagon")  # Depuração
    #             self.overlay.show()
    #     else:
    #         if self.overlay.isVisible():
    #             print("Hiding hexagon")  # Depuração
    #             self.overlay.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FullScreenApp()
    window.show()
    sys.exit(app.exec())
