# ui_components.py

import random
from PyQt6.QtCore import (QUrl, QTimer, Qt, QTime, QDate, QLocale)
from PyQt6.QtGui import (QPainter, QColor, QPixmap)
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGraphicsDropShadowEffect, QSizePolicy, QStackedWidget)

from config import INTERVALO_CARROSSEL
from utils import criar_qr_code
from workers import BaixadorNoticias, BaixadorAvisos, BaixadorImagem

class ClockWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("color: white; font-size: 14pt; font-weight: bold;")
        timer = QTimer(self); timer.timeout.connect(self.update_time); timer.start(1000)
        self.update_time()

    def update_time(self):
        locale_pt_br = QLocale(QLocale.Language.Portuguese, QLocale.Country.Brazil)
        data_str = locale_pt_br.toString(QDate.currentDate(), "dddd, dd 'de' MMMM 'de' yyyy")
        hora_str = QTime.currentTime().toString("HH:mm")
        self.setText(f"{data_str.capitalize()} | {hora_str}")

class CarrosselNoticias(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entradas_noticias = []
        self.entradas_avisos = []
        self.conteudo_combinado = []
        self.indice_atual = 0
        self.noticias_carregadas = False
        self.avisos_carregados = False
        self.baixador_imagem_thread = None

        self.setStyleSheet("""
            #container_noticia, #container_aviso { background-color: #ffffff; border-radius: 15px; }
            #titulo { font-size: 22pt; font-weight: bold; color: #005a9e; }
            #data { font-size: 12pt; color: #555555; font-style: italic; }
            #descricao { font-size: 16pt; color: #333333; }
            #imagem_placeholder { background-color: #eeeeee; border-radius: 10px; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        self.display_stack = QStackedWidget()
        main_layout.addWidget(self.display_stack, 1)

        self.widget_noticia = self._criar_widget_noticia()
        self.display_stack.addWidget(self.widget_noticia)
        self.widget_aviso = self._criar_widget_aviso()
        self.display_stack.addWidget(self.widget_aviso)
        
        self.timer_carrossel = QTimer(self)
        self.timer_carrossel.timeout.connect(self.proximo_item)
        
        self.atualizar_conteudo()

    def _criar_widget_noticia(self):
        container_noticia = QWidget(objectName="container_noticia")
        layout_noticias = QHBoxLayout(container_noticia)
        layout_noticias.setContentsMargins(40, 40, 40, 40); layout_noticias.setSpacing(40)
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(25); shadow.setXOffset(0); shadow.setYOffset(5); shadow.setColor(QColor(0, 0, 0, 60))
        container_noticia.setGraphicsEffect(shadow)
        self.rotulo_imagem_noticia = QLabel("Carregando..."); self.rotulo_imagem_noticia.setObjectName("imagem_placeholder"); self.rotulo_imagem_noticia.setAlignment(Qt.AlignmentFlag.AlignCenter); self.rotulo_imagem_noticia.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        container_texto = QWidget(); container_texto.setStyleSheet("background: transparent;")
        layout_texto = QVBoxLayout(container_texto)
        self.rotulo_titulo = QLabel("Carregando...", objectName="titulo"); self.rotulo_titulo.setWordWrap(True)
        self.rotulo_data = QLabel("", objectName="data"); self.rotulo_data.setWordWrap(True)
        self.rotulo_descricao = QLabel("", objectName="descricao"); self.rotulo_descricao.setWordWrap(True); self.rotulo_descricao.setAlignment(Qt.AlignmentFlag.AlignJustify)
        container_qr = QWidget(); layout_qr = QHBoxLayout(container_qr); layout_qr.setContentsMargins(0, 0, 0, 0)
        self.rotulo_qr = QLabel(); self.rotulo_qr.setFixedSize(150, 150)
        layout_qr.addStretch(); layout_qr.addWidget(self.rotulo_qr)
        layout_texto.addWidget(self.rotulo_titulo); layout_texto.addSpacing(10); layout_texto.addWidget(self.rotulo_data); layout_texto.addSpacing(25); layout_texto.addWidget(self.rotulo_descricao); layout_texto.addStretch(1); layout_texto.addWidget(container_qr)
        layout_noticias.addWidget(self.rotulo_imagem_noticia, 2); layout_noticias.addWidget(container_texto, 3)
        return container_noticia

    def _criar_widget_aviso(self):
        container_aviso = QWidget(objectName="container_aviso")
        layout = QVBoxLayout(container_aviso)
        layout.setContentsMargins(15, 15, 15, 15)
        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(25); shadow.setXOffset(0); shadow.setYOffset(5); shadow.setColor(QColor(0, 0, 0, 60))
        container_aviso.setGraphicsEffect(shadow)
        self.rotulo_imagem_aviso = QLabel("Carregando aviso..."); self.rotulo_imagem_aviso.setAlignment(Qt.AlignmentFlag.AlignCenter); self.rotulo_imagem_aviso.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.rotulo_imagem_aviso.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.rotulo_imagem_aviso)
        return container_aviso
    
    def atualizar_conteudo(self):
        self.timer_carrossel.stop()
        self.noticias_carregadas = False; self.avisos_carregados = False
        self.baixador_noticias = BaixadorNoticias(); self.baixador_noticias.noticias_prontas.connect(self.quando_noticias_prontas); self.baixador_noticias.start()
        self.baixador_avisos = BaixadorAvisos(); self.baixador_avisos.avisos_prontos.connect(self.quando_avisos_prontos); self.baixador_avisos.start()

    def quando_noticias_prontas(self, entradas):
        self.entradas_noticias = entradas; self.noticias_carregadas = True
        self.tentar_combinar_conteudo()

    def quando_avisos_prontos(self, entradas):
        self.entradas_avisos = entradas; self.avisos_carregados = True
        self.tentar_combinar_conteudo()

    def tentar_combinar_conteudo(self):
        if self.noticias_carregadas and self.avisos_carregados:
            self.conteudo_combinado = self.entradas_avisos + self.entradas_noticias
            
            if not self.conteudo_combinado:
                self.display_stack.setCurrentWidget(self.widget_noticia)
                self.rotulo_titulo.setText("Sem conteúdo para exibir"); self.rotulo_descricao.setText("Não foram encontradas notícias ou avisos válidos no momento."); self.rotulo_imagem_noticia.setText("")
                return
                
            self.indice_atual = -1
            self.proximo_item()
            self.timer_carrossel.start(INTERVALO_CARROSSEL * 1000)
    
    def proximo_item(self):
        if self.conteudo_combinado:
            self.indice_atual = (self.indice_atual + 1) % len(self.conteudo_combinado)
            self.exibir_item_atual()

    def exibir_item_atual(self):
        if not self.conteudo_combinado: return
        if self.baixador_imagem_thread and self.baixador_imagem_thread.isRunning(): self.baixador_imagem_thread.terminate()
        item_atual = self.conteudo_combinado[self.indice_atual]
        self.baixador_imagem_thread = BaixadorImagem(item_atual.get('url_imagem'))
        if item_atual['type'] == 'noticia':
            self.display_stack.setCurrentWidget(self.widget_noticia)
            self.rotulo_titulo.setText(item_atual['titulo']); self.rotulo_data.setText(item_atual.get('data', ''))
            desc_html = item_atual['descricao']
            if desc_html.endswith("... - "): desc_html += "<i>Leia a notícia completa no QR Code abaixo.</i>"
            self.rotulo_descricao.setText(desc_html); self.rotulo_qr.setPixmap(criar_qr_code(item_atual['link']) if item_atual['link'] else QPixmap())
            self.rotulo_imagem_noticia.setText("Carregando Imagem...")
            self.baixador_imagem_thread.imagem_pronta.connect(self.exibir_imagem_noticia)
        elif item_atual['type'] == 'aviso':
            self.display_stack.setCurrentWidget(self.widget_aviso)
            self.rotulo_imagem_aviso.setText(f"Carregando: {item_atual.get('titulo', 'Aviso')}")
            self.baixador_imagem_thread.imagem_pronta.connect(self.exibir_imagem_aviso)
        self.baixador_imagem_thread.start()

    def exibir_imagem_noticia(self, pixmap):
        if not pixmap.isNull():
            img = pixmap.scaled(self.rotulo_imagem_noticia.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.rotulo_imagem_noticia.setPixmap(img)
        else:
            self.rotulo_imagem_noticia.setText("Sem imagem")

    def exibir_imagem_aviso(self, pixmap):
        if not pixmap.isNull():
            img = pixmap.scaled(self.rotulo_imagem_aviso.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.rotulo_imagem_aviso.setPixmap(img)
        else:
            self.rotulo_imagem_aviso.setText("Imagem não disponível")

class MenuLateral(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget { background-color: #fdfdfd; }
            QPushButton { 
                font-size: 13pt; color: #333; background-color: transparent; border: none;
                padding: 15px; text-align: left; border-radius: 8px;
            }
            QPushButton:hover { background-color: #e8f0fe; color: #005a9e; border: none; outline: none; }
            QPushButton:disabled { color: #aaaaaa; background-color: transparent; }
        """)
        layout = QVBoxLayout(self); layout.setContentsMargins(10, 20, 10, 20); layout.setSpacing(8)
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(20); shadow.setColor(QColor(0,0,0,30)); shadow.setOffset(2,0)
        self.setGraphicsEffect(shadow)
        botoes_info = [
            ("inicio", "🏠  Página Inicial"), ("campus", "🏛️  Conheça o Campus"), ("onibus", "🚌  Linha de Ônibus"),
            ("horarios", "⏰  Horário de Aulas"), ("agenda", "📅  Agenda FCT"), ("mapa", "🗺️  Mapa de Salas"),
            ("quiz", "🧠  Quiz FCT (Em breve)"), ("pessoas", "👥  Equipe FCT/UFG"), ("extensao", "🌱  Ações de Extensão")
        ]
        self.botoes = {}
        for chave, texto in botoes_info:
            btn = QPushButton(texto)
            if chave == "quiz": btn.setEnabled(False)
            else: btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.botoes[chave] = btn
            layout.addWidget(btn)
        layout.addStretch()