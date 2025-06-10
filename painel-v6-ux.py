# -------------------------------------------------------------
# PAINEL INTERATIVO FCT
# VERSÃO: 6
# -------------------------------------------------------------

import sys
import requests
import qrcode
import feedparser
import time
import os
import json
from datetime import datetime
from io import BytesIO
from bs4 import BeautifulSoup

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-gpu-compositing"

from PyQt6.QtCore import (QUrl, QTimer, Qt, QThread, pyqtSignal, QEvent)
from PyQt6.QtGui import (QGuiApplication, QPainter, QPixmap, QImage)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QStackedWidget, QScrollArea, QProgressBar)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from typing import List, Dict, Any, Optional

# --- Configurações da Aplicação ---
MENU_INICIAL_VISIVEL = True
URL_FEED = "https://fct.ufg.br/feed"
URL_AVISOS_API = "http://localhost:3000/api/avisos"
QUANTIDADE_NOTICIAS_FEED = 5
INTERVALO_ATUALIZACAO_CONTEUDO = 1800
INTERVALO_AVANCO_CARROSSEL_MS = 20000

# --- Configurações de Rolagem e Texto ---
DELAY_ROLAGEM_MS = 4000
LIMITE_DESCRICAO_CARACTERES = 1200

# --- Constantes de UI ---
LARGURA_MENU_LATERAL = 250
TAMANHO_BOTAO_HAMBURGUER = 50
BREAKPOINT_TELA_PEQUENA = 900

# -------------------------------------------------------------
# COMPONENTE DE GERENCIAMENTO DE CONTEÚDO (NOTÍCIAS E AVISOS)
# (Sem alterações nesta classe)
# -------------------------------------------------------------
class GerenciadorConteudo(QThread):
    conteudo_pronto = pyqtSignal(list)

    def _carregar_avisos_ativos(self) -> List[Dict[str, Any]]:
        avisos_ativos = []
        try:
            response = requests.get(URL_AVISOS_API, timeout=5)
            response.raise_for_status()
            avisos = response.json()
            agora = datetime.now()
            for aviso in avisos:
                try:
                    data_inicio = datetime.strptime(aviso['data_inicio'], '%Y-%m-%d %H:%M')
                    data_fim = datetime.strptime(aviso['data_fim'], '%Y-%m-%d %H:%M')
                    if data_inicio <= agora <= data_fim:
                        avisos_ativos.append({
                            'titulo': aviso['titulo'], 'descricao': aviso['descricao'],
                            'link': aviso.get('link', ''), 'url_imagem': aviso.get('url_imagem'),
                            'data': f"Aviso válido até {data_fim.strftime('%d/%m/%Y às %H:%M')}", 'tipo': 'aviso'
                        })
                except (ValueError, KeyError) as e:
                    print(f"Aviso da API ignorado: {e}")
        except Exception as e:
            print(f"Erro ao carregar avisos: {e}")
        return avisos_ativos

    def _carregar_noticias_feed(self) -> List[Dict[str, Any]]:
        entradas_processadas = []
        try:
            feed = feedparser.parse(URL_FEED)
            for entrada in feed.entries[:QUANTIDADE_NOTICIAS_FEED]:
                sopa_img = BeautifulSoup(entrada.get('description', ''), 'html.parser')
                tag_img = sopa_img.find('img')
                url_imagem = tag_img['src'] if tag_img and tag_img.get('src') else None

                if url_imagem:
                    url_lower = url_imagem.lower()
                    if "fct.ufg.brhttps://" in url_lower or "fct.ufg.brhttp://" in url_lower:
                        start_index = url_lower.find("http", 1)
                        if start_index != -1: url_imagem = url_imagem[start_index:]
                
                sopa_desc = BeautifulSoup(entrada.get('description', ''), 'html.parser')
                for tag in sopa_desc(["script", "style"]): tag.decompose()
                
                descricao = ' '.join(sopa_desc.get_text(separator=' ', strip=True).split())
                titulo = entrada.get('title', '')
                
                hint_message = "<br><br><i>(Leia a notícia completa no QR Code)</i>"
                if len(descricao) > LIMITE_DESCRICAO_CARACTERES:
                    posicao_corte = descricao.rfind(' ', 0, LIMITE_DESCRICAO_CARACTERES)
                    if posicao_corte == -1: posicao_corte = LIMITE_DESCRICAO_CARACTERES
                    descricao = descricao[:posicao_corte] + "..." + hint_message
                
                try:
                    data_parsed = time.strptime(entrada.get('published', ''), "%a, %d %b %Y %H:%M:%S %z")
                    data_formatada = time.strftime("%d/%m/%Y - %H:%M", data_parsed)
                except (ValueError, TypeError): data_formatada = "Data não disponível"
                
                entradas_processadas.append({
                    'titulo': titulo, 'descricao': descricao, 'link': entrada.get('link', ''),
                    'url_imagem': url_imagem, 'data': data_formatada, 'tipo': 'noticia'
                })
        except Exception as e:
            print(f"Erro ao obter notícias do feed: {e}")
        return entradas_processadas

    def run(self):
        avisos = self._carregar_avisos_ativos()
        noticias = self._carregar_noticias_feed()
        conteudo_final = avisos + noticias
        if not conteudo_final: print("Nenhum conteúdo disponível.")
        else: print(f"Conteúdo carregado: {len(avisos)} aviso(s), {len(noticias)} notícia(s).")
        self.conteudo_pronto.emit(conteudo_final)

# -------------------------------------------------------------
# HELPER E WIDGETS AUXILIARES (Sem alterações)
# -------------------------------------------------------------
def criar_qr_code(url, tamanho=150):
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url); qr.make(fit=True)
        img_pil = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO(); img_pil.save(buffer, format='PNG')
        qimagem = QImage.fromData(buffer.getvalue())
        return QPixmap.fromImage(qimagem).scaled(tamanho, tamanho, Qt.AspectRatioMode.KeepAspectRatio)
    except Exception as e:
        print(f"Erro ao criar QR code: {str(e)}"); return QPixmap()

class ImageDownloader(QThread):
    imagem_pronta = pyqtSignal(QPixmap, str)
    def __init__(self, url: str, parent=None): super().__init__(parent); self.url = url
    def run(self):
        try:
            resposta = requests.get(self.url, timeout=10)
            if resposta.status_code == 200:
                pixmap = QPixmap(); pixmap.loadFromData(resposta.content); self.imagem_pronta.emit(pixmap, self.url)
        except Exception as e:
            print(f"Erro no download da imagem '{self.url}': {e}"); self.imagem_pronta.emit(QPixmap(), self.url)

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent); self._pixmap = QPixmap(); self.setAlignment(Qt.AlignmentFlag.AlignCenter); self.setMinimumSize(200, 200)
    def setPixmap(self, pixmap: Optional[QPixmap]): self._pixmap = pixmap if pixmap else QPixmap(); self.update()
    def paintEvent(self, event):
        if not self._pixmap.isNull():
            scaled_pixmap = self._pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled_pixmap.width()) // 2; y = (self.height() - scaled_pixmap.height()) // 2
            painter = QPainter(self); painter.drawPixmap(x, y, scaled_pixmap)
        else: super().paintEvent(event)

# -------------------------------------------------------------
# WIDGET PARA EXIBIÇÃO DO CONTEÚDO (CARROSSEL)
# -------------------------------------------------------------
class CarrosselConteudo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.itens_carrossel = []
        self.indice_atual = 0
        self.image_downloader = None
        self.is_layout_vertical = None
        self.passo_rolagem = 0
        self.posicao_rolagem_flutuante = 0.0

        main_layout = QVBoxLayout(self)
        self.conteiner_conteudo = QWidget()
        main_layout.addWidget(self.conteiner_conteudo, 1)
        self.layout_horizontal = QHBoxLayout()
        self.layout_vertical = QVBoxLayout()
        self.rotulo_imagem = ImageLabel()
        self.rotulo_imagem.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd; border-radius: 10px;")
        self.conteiner_texto = QWidget()
        self.layout_texto = QVBoxLayout(self.conteiner_texto)
        self.rotulo_titulo = QLabel("Carregando conteúdo...")
        self.rotulo_titulo.setWordWrap(True)
        self.rotulo_data = QLabel("")
        self.rotulo_data.setWordWrap(True)
        self.area_rolagem_descricao = QScrollArea()
        self.area_rolagem_descricao.setWidgetResizable(True)
        self.area_rolagem_descricao.setFrameShape(QScrollArea.Shape.NoFrame)
        self.area_rolagem_descricao.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.area_rolagem_descricao.setStyleSheet("background: transparent; border: none;")
        self.rotulo_descricao = QLabel()
        self.rotulo_descricao.setWordWrap(True)
        self.rotulo_descricao.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignJustify)
        self.rotulo_descricao.setStyleSheet("background: transparent;")
        self.area_rolagem_descricao.setWidget(self.rotulo_descricao)
        self.conteiner_qr = QWidget()
        self.layout_qr = QHBoxLayout(self.conteiner_qr)
        self.layout_qr.setContentsMargins(0, 10, 0, 0)
        self.rotulo_qr = QLabel()
        self.rotulo_qr.setFixedSize(150, 150)
        self.layout_qr.addStretch()
        self.layout_qr.addWidget(self.rotulo_qr)
        self.layout_texto.addWidget(self.rotulo_titulo)
        self.layout_texto.addWidget(self.rotulo_data)
        self.layout_texto.addWidget(self.area_rolagem_descricao, 1)
        self.layout_texto.addWidget(self.conteiner_qr)
        self.barra_progresso = QProgressBar()
        self.barra_progresso.setFixedHeight(4)
        self.barra_progresso.setTextVisible(False)
        self.barra_progresso.setStyleSheet("""
            QProgressBar { border: none; background-color: transparent; }
            QProgressBar::chunk { background-color: #0072b9; }
        """)
        main_layout.addWidget(self.barra_progresso)
        self.timer_carrossel = QTimer(self)
        self.timer_carrossel.timeout.connect(self.proximo_item)
        self.timer_progresso = QTimer(self)
        self.timer_progresso.timeout.connect(self._atualizar_progresso)
        self.timer_rolagem_descricao = QTimer(self)
        self.timer_rolagem_descricao.timeout.connect(self._rolar_descricao_suave)
        self.gerenciador_conteudo = GerenciadorConteudo()
        self.gerenciador_conteudo.conteudo_pronto.connect(self.quando_conteudo_pronto)
        self.gerenciador_conteudo.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.ajustar_layout_responsivo()
        self.atualizar_fontes_dinamicas()

    def ajustar_layout_responsivo(self):
        largura = self.width()
        if largura < BREAKPOINT_TELA_PEQUENA and not self.is_layout_vertical:
            self.is_layout_vertical = True
            while self.layout_horizontal.count(): self.layout_horizontal.takeAt(0).widget().setParent(None)
            self.layout_vertical.addWidget(self.rotulo_imagem)
            self.layout_vertical.addWidget(self.conteiner_texto)
            self.conteiner_conteudo.setLayout(self.layout_vertical)
        elif largura >= BREAKPOINT_TELA_PEQUENA and (self.is_layout_vertical or self.is_layout_vertical is None):
            self.is_layout_vertical = False
            while self.layout_vertical.count(): self.layout_vertical.takeAt(0).widget().setParent(None)
            # ### MUDANÇA: Proporção restaurada para 2:3 (40%/60%) para imagem e texto ###
            self.layout_horizontal.addWidget(self.rotulo_imagem, 2)
            self.layout_horizontal.addWidget(self.conteiner_texto, 3)
            self.conteiner_conteudo.setLayout(self.layout_horizontal)

    def atualizar_fontes_dinamicas(self):
        altura_widget = self.height()
        if altura_widget == 0: return
        fator = max(0.8, altura_widget / 1080.0)
        def get_fs(tamanho_base): return int(tamanho_base * fator)
        self.rotulo_titulo.setStyleSheet(f"font-size: {get_fs(36)}px; font-weight: bold; color: #0072b9;")
        self.rotulo_data.setStyleSheet(f"font-size: {get_fs(20)}px; color: #555; font-style: italic;")
        self.rotulo_descricao.setStyleSheet(f"font-size: {get_fs(30)}px; color: #333; padding-right: 15px;")

    def quando_conteudo_pronto(self, itens):
        self.itens_carrossel = itens
        if itens:
            self.indice_atual = 0
            self.atualizar_exibicao()
            self.timer_carrossel.start(INTERVALO_AVANCO_CARROSSEL_MS) 
            self.timer_progresso.start(100)
        else:
            self.rotulo_titulo.setText("Não foi possível carregar conteúdo.")
            self.rotulo_descricao.setText("Verifique a conexão com a internet.")

    def atualizar_exibicao(self):
        if not self.itens_carrossel: return
        self.timer_rolagem_descricao.stop()
        item = self.itens_carrossel[self.indice_atual]
        self.rotulo_titulo.setText(item['titulo'])
        self.rotulo_data.setText(item.get('data', ''))
        self.rotulo_descricao.setText(item['descricao'])
        self.area_rolagem_descricao.verticalScrollBar().setValue(0)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setMaximum(INTERVALO_AVANCO_CARROSSEL_MS)
        QTimer.singleShot(100, self._configurar_e_iniciar_rolagem)
        self.rotulo_qr.setPixmap(criar_qr_code(item['link']) if item.get('link') else QPixmap())
        self.conteiner_qr.setVisible(bool(item.get('link')))
        if item.get('url_imagem'): self.baixar_imagem(item['url_imagem'])
        else: self.rotulo_imagem.setText("Sem imagem disponível"); self.rotulo_imagem.setPixmap(None)

    def baixar_imagem(self, url):
        self.rotulo_imagem.setText("Carregando imagem..."); self.rotulo_imagem.setPixmap(None)
        self.image_downloader = ImageDownloader(url)
        self.image_downloader.imagem_pronta.connect(self.on_imagem_baixada); self.image_downloader.start()

    def on_imagem_baixada(self, pixmap, url_original):
        if not self.itens_carrossel: return
        if self.itens_carrossel[self.indice_atual].get('url_imagem') == url_original:
            if pixmap.isNull(): self.rotulo_imagem.setText("Erro ao carregar imagem")
            else: self.rotulo_imagem.setText(""); self.rotulo_imagem.setPixmap(pixmap)
    
    def proximo_item(self):
        if self.itens_carrossel:
            self.indice_atual = (self.indice_atual + 1) % len(self.itens_carrossel)
            self.atualizar_exibicao()
    
    def atualizar_conteudo(self):
        print("Iniciando atualização de conteúdo...")
        for timer in [self.timer_carrossel, self.timer_progresso, self.timer_rolagem_descricao]: timer.stop()
        self.gerenciador_conteudo = GerenciadorConteudo()
        self.gerenciador_conteudo.conteudo_pronto.connect(self.quando_conteudo_pronto); self.gerenciador_conteudo.start()

    def _configurar_e_iniciar_rolagem(self):
        scrollbar = self.area_rolagem_descricao.verticalScrollBar()
        distancia_total = scrollbar.maximum()
        if distancia_total <= 0:
            self.passo_rolagem = 0
            return
        tempo_total_rolagem = INTERVALO_AVANCO_CARROSSEL_MS - DELAY_ROLAGEM_MS
        if tempo_total_rolagem <= 0:
            self.passo_rolagem = 0
            return
        intervalo_timer_ms = 50
        numero_de_passos = tempo_total_rolagem / intervalo_timer_ms
        self.passo_rolagem = distancia_total / numero_de_passos if numero_de_passos > 0 else 0
        self.posicao_rolagem_flutuante = 0.0
        QTimer.singleShot(DELAY_ROLAGEM_MS, self._iniciar_rolagem_agendada)

    def _iniciar_rolagem_agendada(self):
        if self.passo_rolagem > 0: self.timer_rolagem_descricao.start(50)

    def _rolar_descricao_suave(self):
        scrollbar = self.area_rolagem_descricao.verticalScrollBar()
        if scrollbar.value() >= scrollbar.maximum():
            self.timer_rolagem_descricao.stop()
            return
        self.posicao_rolagem_flutuante += self.passo_rolagem
        scrollbar.setValue(int(self.posicao_rolagem_flutuante))
            
    def _atualizar_progresso(self):
        valor_atual = self.barra_progresso.value()
        intervalo = self.timer_progresso.interval()
        self.barra_progresso.setValue(valor_atual + intervalo)

# -------------------------------------------------------------
# DEMAIS CLASSES (MenuLateral, AplicacaoTelaCheia) - Sem alterações
# -------------------------------------------------------------
class MenuLateral(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QWidget {{ background-color: #F5F5F5; border-radius: 10px; }}
            QPushButton {{ 
                font-size: 18px; color: #424242; background: transparent; 
                border: none; padding: 12px; text-align: left; 
                border-left: 5px solid transparent;
            }}
            QPushButton:hover {{ background-color: #E0E0E0; }}
            QPushButton[active="true"] {{
                color: #0072b9; font-weight: bold;
                border-left: 5px solid #0072b9;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 20, 5, 20)
        layout.setSpacing(10)
        self.botoes = {
            "inicio": QPushButton("🏠  Página Inicial"), "campus": QPushButton("🏛️  Conheça o Campus"),
            "onibus": QPushButton("🚌  Linha de Ônibus"), "horarios": QPushButton("⏰  Horário de Aulas"),
            "mapa": QPushButton("🗺️  Mapa de Salas"), "pessoas": QPushButton("👥  Equipe FCT/UFG"),
            "extensao": QPushButton("🌱  Ações de Extensão")
        }
        for nome, btn in self.botoes.items():
            btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.setProperty("id", nome); layout.addWidget(btn)
        layout.addStretch()

class AplicacaoTelaCheia(QMainWindow):
    def __init__(self):
        super().__init__()
        QGuiApplication.instance().installEventFilter(self)
        self.setWindowTitle("Painel Interativo FCT")
        self.setCentralWidget(QWidget())
        layout_principal = QVBoxLayout(self.centralWidget())
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)
        cabecalho = self._criar_cabecalho()
        layout_principal.addWidget(cabecalho)
        layout_conteudo = QHBoxLayout()
        layout_conteudo.setContentsMargins(10, 10, 10, 10)
        layout_conteudo.setSpacing(10)
        self.menu_lateral = MenuLateral()
        self.menu_visivel = MENU_INICIAL_VISIVEL
        self.menu_lateral.setFixedWidth(LARGURA_MENU_LATERAL if self.menu_visivel else 0)
        layout_conteudo.addWidget(self.menu_lateral)
        self.area_conteudo = QStackedWidget()
        self.carrossel_conteudo = CarrosselConteudo()
        self.webview = QWebEngineView()
        self.webview.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        self.webview.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        self.area_conteudo.addWidget(self.carrossel_conteudo)
        self.area_conteudo.addWidget(self.webview)
        self.area_conteudo.setCurrentWidget(self.carrossel_conteudo)
        layout_conteudo.addWidget(self.area_conteudo)
        layout_principal.addLayout(layout_conteudo)
        self._conectar_sinais()
        self.atualizar_destaque_menu("inicio")
        self.timer_inatividade = QTimer(self)
        self.timer_inatividade.setInterval(60000)
        self.timer_inatividade.timeout.connect(self.voltar_para_home)
        self.timer_inatividade.start()
        self.timer_atualizacao = QTimer(self)
        self.timer_atualizacao.timeout.connect(self.atualizar_conteudo)
        self.timer_atualizacao.start(INTERVALO_ATUALIZACAO_CONTEUDO * 1000)
        self.showFullScreen()
        self.setMouseTracking(True)
        
    def _criar_cabecalho(self):
        cabecalho = QWidget()
        cabecalho.setStyleSheet("background-color: #0072b9;")
        layout = QHBoxLayout(cabecalho)
        layout.setContentsMargins(10, 10, 10, 10)
        self.btn_hamburger = QPushButton("☰")
        self.btn_hamburger.setFixedSize(TAMANHO_BOTAO_HAMBURGUER, TAMANHO_BOTAO_HAMBURGUER)
        self.btn_hamburger.setStyleSheet("""
            QPushButton { background-color: transparent; color: white; border: none; font-size: 30px; }
            QPushButton:hover { background-color: #2096f3; }
        """)
        self.btn_hamburger.clicked.connect(self.alternar_menu)
        layout.addWidget(self.btn_hamburger)
        titulo = QLabel("Painel Interativo FCT/UFG")
        titulo.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo, 1)
        espacador_direito = QWidget()
        espacador_direito.setFixedSize(TAMANHO_BOTAO_HAMBURGUER, TAMANHO_BOTAO_HAMBURGUER)
        layout.addWidget(espacador_direito)
        return cabecalho

    def _conectar_sinais(self):
        menu = self.menu_lateral.botoes
        menu["inicio"].clicked.connect(lambda: self.mostrar_pagina("inicio"))
        menu["campus"].clicked.connect(lambda: self.mostrar_pagina("campus", "https://prezi.com/view/MZjulFdzyMstq9zoDLVX/"))
        menu["onibus"].clicked.connect(lambda: self.mostrar_pagina("onibus", "https://rmtcgoiania.com.br/index.php/linhas-e-trajetos/area-sul?buscar=555"))
        menu["horarios"].clicked.connect(lambda: self.mostrar_pagina("horarios", "https://ti-fct.github.io/horariosFCT/"))
        menu["mapa"].clicked.connect(lambda: self.mostrar_pagina("mapa", "https://ti-fct.github.io/Painel-FCT/mapa.html"))
        menu["pessoas"].clicked.connect(lambda: self.mostrar_pagina("pessoas", "https://app.powerbi.com/view?r=eyJrIjoiNjUzMDMzOWUtNzViNS00NGYyLTk1YTYtMWY5MWE5OGI1YzAzIiwidCI6ImIxY2E3YTgxLWFiZjgtNDJlNS05OGM2LWYyZjJhOTMwYmEzNiJ9"))
        menu["extensao"].clicked.connect(lambda: self.mostrar_pagina("extensao", "https://app.powerbi.com/view?r=eyJrIjoiMDcyZWQ2NWMtZTVkMy00YzMyLTkyYjQtNzFmMjQ1MzVjZDcwIiwidCI6ImIxY2E3YTgxLWFiZjgtNDJlNS05OGM2LWYyZjJhOTMwYmEzNiJ9"))

    def mostrar_pagina(self, nome_botao: str, url: Optional[str] = None):
        self.atualizar_destaque_menu(nome_botao)
        if url: self.webview.load(QUrl(url)); self.area_conteudo.setCurrentWidget(self.webview)
        else: self.area_conteudo.setCurrentWidget(self.carrossel_conteudo)

    def atualizar_destaque_menu(self, nome_botao_ativo: str):
        for nome, botao in self.menu_lateral.botoes.items():
            ativo = (nome == nome_botao_ativo); botao.setProperty("active", ativo)
            botao.style().unpolish(botao); botao.style().polish(botao)

    def alternar_menu(self):
        largura_alvo = 0 if self.menu_visivel else LARGURA_MENU_LATERAL
        self.menu_lateral.setFixedWidth(largura_alvo); self.menu_visivel = not self.menu_visivel
    
    def voltar_para_home(self): self.mostrar_pagina("inicio")
    
    def atualizar_conteudo(self):
        if self.area_conteudo.currentWidget() == self.carrossel_conteudo:
            self.carrossel_conteudo.atualizar_conteudo()
    
    def eventFilter(self, fonte, evento):
        if evento.type() in (QEvent.Type.MouseMove, QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress):
            self.timer_inatividade.start()
        return super().eventFilter(fonte, evento)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = AplicacaoTelaCheia()
    janela.show()
    sys.exit(app.exec())