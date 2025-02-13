import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QPushButton)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QKeySequence

class FullScreenApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configurar janela principal
        self.setWindowTitle("Painel Interativo FCT")
        self.showFullScreen()
        
        # Criar widget central e layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setStretch(1, 1)
        
        # Criar menu superior
        menu = QWidget()
        menu_layout = QHBoxLayout(menu)
        menu_layout.setSpacing(20)
        menu.setFixedHeight(60)  # Altura fixa para o menu
        
        # Botões do menu
        self.btn_home = QPushButton("Home")
        self.btn_horarios = QPushButton("Horários")
        self.btn_fct_numeros = QPushButton("FCT em Números")
        
        # Adicionar botões ao menu
        for btn in [self.btn_home, self.btn_horarios, self.btn_fct_numeros]:
            menu_layout.addWidget(btn)
        
        # Área de visualização web
        self.webview = QWebEngineView()
        
        # Adicionar elementos ao layout principal
        layout.addWidget(menu)
        layout.addWidget(self.webview)
        
        # Estilização
        self.setStyleSheet("""
            QWidget {
                background-color: #1a237e;
            }
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 20px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #2196f3;
            }
        """)
        
        # Conectar botões
        self.btn_home.clicked.connect(lambda: self.carregar_url("https://fct.ufg.br"))
        self.btn_horarios.clicked.connect(lambda: self.carregar_url("https://www.g1.com.br/"))
        self.btn_fct_numeros.clicked.connect(lambda: self.carregar_url("https://www.uol.com.br"))
        
        # Carregar página inicial
        self.carregar_url("https://ufg.br")
        
    def carregar_url(self, url):
        self.webview.load(QUrl(url))
        
    def keyPressEvent(self, event):
        # Bloquear atalhos de fechamento
        if event.matches(QKeySequence.Close):
            event.ignore()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FullScreenApp()
    sys.exit(app.exec_())