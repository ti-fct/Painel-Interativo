# main.py

import sys
import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"

from PyQt6.QtCore import (QUrl, QTimer, Qt, QEvent, QPropertyAnimation, QEasingCurve, QPoint, 
                          QSequentialAnimationGroup)
from PyQt6.QtGui import QGuiApplication, QPainter, QBrush, QColor, QPen, QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QStackedWidget, QGraphicsDropShadowEffect)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

from config import (INTERVALO_ATUALIZACAO_AVISOS, URLS, LARGURA_MENU, 
                    MODO_TELA_CHEIA, ANIMACAO_BOLINHA_ATIVA)
from ui_components import CarrosselNoticias, MenuLateral, ClockWidget

class BolinhaAnimada(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.raio = 80
        self.cor_bolinha = QColor("#005a9e"); self.cor_bolinha.setAlphaF(0.85)
        self.mensagem = "Olá, utilize\no mouse abaixo\npara interagir"
        self.fonte_texto = QFont("Arial", 12, QFont.Weight.Bold)
        self.setFixedSize(self.raio * 2, self.raio * 2)
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(20); shadow.setColor(QColor(0,0,0,90))
        self.setGraphicsEffect(shadow)
        self._configurar_animacao()
        self.hide()

    def _configurar_animacao(self):
        self.animacao_grupo = QSequentialAnimationGroup(self); self.animacao_grupo.setLoopCount(-1)
        anim1 = QPropertyAnimation(self, b"pos"); anim1.setDuration(4000)
        anim2 = QPropertyAnimation(self, b"pos"); anim2.setDuration(4000)
        anim3 = QPropertyAnimation(self, b"pos"); anim3.setDuration(4000)
        anim4 = QPropertyAnimation(self, b"pos"); anim4.setDuration(4000)
        self.animacao_grupo.addAnimation(anim1); self.animacao_grupo.addAnimation(anim2)
        self.animacao_grupo.addAnimation(anim3); self.animacao_grupo.addAnimation(anim4)

    def paintEvent(self, evento):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(self.cor_bolinha)); painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(0, 0, self.raio * 2, self.raio * 2)
        painter.setPen(QPen(Qt.GlobalColor.white)); painter.setFont(self.fonte_texto)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.mensagem)

    def start_animation(self):
        w_pai, h_pai = self.parent().width(), self.parent().height(); borda = self.raio * 2
        anim1 = self.animacao_grupo.animationAt(0); anim1.setStartValue(QPoint(borda, borda)); anim1.setEndValue(QPoint(w_pai - borda, h_pai - borda)); anim1.setEasingCurve(QEasingCurve.Type.InOutSine)
        anim2 = self.animacao_grupo.animationAt(1); anim2.setEndValue(QPoint(w_pai - borda, borda)); anim2.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim3 = self.animacao_grupo.animationAt(2); anim3.setEndValue(QPoint(borda, h_pai - borda)); anim3.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim4 = self.animacao_grupo.animationAt(3); anim4.setEndValue(QPoint(borda, borda)); anim4.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.show(); self.raise_(); self.animacao_grupo.start()

    def stop_animation(self):
        self.animacao_grupo.stop(); self.hide()

class AplicacaoPainel(QMainWindow):
    def __init__(self):
        super().__init__()
        QGuiApplication.instance().installEventFilter(self)
        self.setWindowTitle("Painel Interativo FCT/UFG"); self.setStyleSheet("background-color: #f0f2f5;")
        widget_central = QWidget(); self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central); layout_principal.setContentsMargins(0, 0, 0, 0); layout_principal.setSpacing(0)
        layout_principal.addWidget(self._criar_cabecalho())
        layout_conteudo = QHBoxLayout(); layout_conteudo.setContentsMargins(0, 0, 0, 0); layout_conteudo.setSpacing(0)
        self.menu_lateral = MenuLateral()
        self.menu_visivel = True
        self.menu_lateral.setMaximumWidth(LARGURA_MENU)
        layout_conteudo.addWidget(self.menu_lateral)
        self.area_conteudo = QStackedWidget()
        self.carrossel_conteudo = CarrosselNoticias()
        self.webview = self._criar_webview()
        self.area_conteudo.addWidget(self.carrossel_conteudo); self.area_conteudo.addWidget(self.webview)
        self.area_conteudo.setCurrentWidget(self.carrossel_conteudo)
        layout_conteudo.addWidget(self.area_conteudo, 1)
        layout_principal.addLayout(layout_conteudo)
        self._conectar_sinais(); self._iniciar_timers()
        self.bolinha = None
        if ANIMACAO_BOLINHA_ATIVA:
            self.bolinha = BolinhaAnimada(self)
    
    def _criar_cabecalho(self) -> QWidget:
        cabecalho = QWidget(); cabecalho.setFixedHeight(60); cabecalho.setStyleSheet("background-color: #005a9e; padding: 0 10px;")
        layout_cabecalho = QHBoxLayout(cabecalho)
        self.btn_hamburger = QPushButton("☰"); self.btn_hamburger.setFixedSize(40, 40); self.btn_hamburger.setCursor(Qt.CursorShape.PointingHandCursor); self.btn_hamburger.setStyleSheet("background: transparent; color: white; border: none; font-size: 28px;")
        titulo = QLabel("Painel Interativo FCT/UFG"); titulo.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        self.relogio = ClockWidget()
        layout_cabecalho.addWidget(self.btn_hamburger); layout_cabecalho.addWidget(titulo); layout_cabecalho.addStretch(); layout_cabecalho.addWidget(self.relogio)
        return cabecalho

    def _criar_webview(self) -> QWebEngineView:
        view = QWebEngineView()
        settings = view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        return view

    def _conectar_sinais(self):
        self.btn_hamburger.clicked.connect(self.alternar_menu)
        botoes = self.menu_lateral.botoes
        botoes["inicio"].clicked.connect(self.mostrar_inicio)
        for nome_botao, botao_widget in botoes.items():
            if nome_botao in URLS:
                url_para_conectar = URLS[nome_botao]
                botao_widget.clicked.connect(lambda checked, url=url_para_conectar: self.carregar_url(url))

    def _iniciar_timers(self):
        self.timer_atualizacao_conteudo = QTimer(self); self.timer_atualizacao_conteudo.timeout.connect(self.carrossel_conteudo.atualizar_conteudo)
        self.timer_atualizacao_conteudo.start(INTERVALO_ATUALIZACAO_AVISOS * 1000)
        
        self.timer_inatividade = QTimer(self)
        # MUDANÇA: Intervalo alterado para 2 minutos (2 * 60 * 1000 = 120000 ms).
        self.timer_inatividade.setInterval(120000)
        self.timer_inatividade.timeout.connect(self.voltar_para_home)
        self.timer_inatividade.start()

    def alternar_menu(self):
        largura_alvo = 0 if self.menu_visivel else LARGURA_MENU; self.menu_visivel = not self.menu_visivel
        self.animacao_menu = QPropertyAnimation(self.menu_lateral, b"maximumWidth"); self.animacao_menu.setDuration(300); self.animacao_menu.setStartValue(self.menu_lateral.width()); self.animacao_menu.setEndValue(largura_alvo); self.animacao_menu.setEasingCurve(QEasingCurve.Type.InOutCubic); self.animacao_menu.start()

    def abrir_menu(self):
        """Garante que o menu lateral esteja aberto, sem alterná-lo se já estiver."""
        if not self.menu_visivel:
            self.alternar_menu()

    def voltar_para_home(self):
        """Retorna o painel para seu estado inicial após inatividade."""
        self.mostrar_inicio() 
        self.abrir_menu()     
        
        if self.bolinha:
            self.bolinha.start_animation() 

    def mostrar_inicio(self):
        self.area_conteudo.setCurrentWidget(self.carrossel_conteudo)

    def carregar_url(self, url: str):
        self.webview.load(QUrl(url))
        self.area_conteudo.setCurrentWidget(self.webview)

    def eventFilter(self, fonte, evento) -> bool:
        if evento.type() in (QEvent.Type.MouseMove, QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress):
            if self.bolinha:
                self.bolinha.stop_animation()
            self.timer_inatividade.start()
        return super().eventFilter(fonte, evento)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = AplicacaoPainel()
    if MODO_TELA_CHEIA: janela.showFullScreen()
    else: janela.showMaximized()
    sys.exit(app.exec())