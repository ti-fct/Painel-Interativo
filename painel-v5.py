# -------------------------------------------------------------
# PAINEL INTERATIVO FCT
# VERSÃO: 5.0 - Atualizado com Avisos Personalizados e Melhorias
# -------------------------------------------------------------

import sys
import requests
import qrcode
import feedparser
import time
import os
import json
import random
from datetime import datetime
from io import BytesIO
from bs4 import BeautifulSoup

# Configurações para QtWebEngine (mantido)
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-gpu-compositing"

from PyQt6.QtCore import (QUrl, QTimer, Qt, QThread, pyqtSignal, QEvent, QRectF)
from PyQt6.QtGui import (QGuiApplication, QPainter, QColor, QPixmap, QImage, QFont, QTextOption)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QSizePolicy, QStackedWidget)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from typing import List, Dict, Any

# --- Configurações da Aplicação ---
MENU_INICIAL_VISIVEL = True
ANIMACAO_BOLINHA_ATIVA = False
URL_FEED = "https://fct.ufg.br/feed"
ARQUIVO_AVISOS = "avisos.json"  # Nome do arquivo de avisos
LIMITE_TITULO = 90
LIMITE_DESCRICAO = 400
INTERVALO_ATUALIZACAO_CONTEUDO = 3600  # 1 hora em segundos
LARGURA_IMAGEM = 500
ALTURA_IMAGEM = 600

# -------------------------------------------------------------
# COMPONENTE DE GERENCIAMENTO DE CONTEÚDO (NOTÍCIAS E AVISOS)
# -------------------------------------------------------------
class GerenciadorConteudo(QThread):
    """
    Thread responsável por baixar notícias do feed RSS e carregar
    avisos de um arquivo JSON local, misturando-os para exibição.
    """
    conteudo_pronto = pyqtSignal(list)

    def _carregar_avisos_ativos(self) -> List[Dict[str, Any]]:
        """Lê o arquivo JSON, filtra e retorna os avisos ativos."""
        avisos_ativos = []
        try:
            with open(ARQUIVO_AVISOS, 'r', encoding='utf-8') as f:
                avisos = json.load(f)
            
            agora = datetime.now()
            
            for aviso in avisos:
                try:
                    data_inicio = datetime.strptime(aviso['data_inicio'], '%Y-%m-%d %H:%M')
                    data_fim = datetime.strptime(aviso['data_fim'], '%Y-%m-%d %H:%M')
                    
                    # Verifica se o aviso está no período de validade
                    if data_inicio <= agora <= data_fim:
                        # Formata a data de exibição para algo amigável
                        data_exibicao = f"Aviso válido até {data_fim.strftime('%d/%m/%Y às %H:%M')}"
                        
                        aviso_processado = {
                            'titulo': aviso['titulo'],
                            'descricao': aviso['descricao'],
                            'link': aviso.get('link', ''),
                            'url_imagem': aviso.get('url_imagem'),
                            'data': data_exibicao,
                            'tipo': 'aviso' # Identificador interno
                        }
                        avisos_ativos.append(aviso_processado)

                except (ValueError, KeyError) as e:
                    print(f"Aviso ignorado por erro de formato/chave: {aviso.get('titulo', 'Sem Título')}. Erro: {e}")

        except FileNotFoundError:
            print(f"Arquivo '{ARQUIVO_AVISOS}' não encontrado. Nenhum aviso será carregado.")
        except json.JSONDecodeError:
            print(f"Erro ao decodificar o arquivo JSON '{ARQUIVO_AVISOS}'. Verifique a formatação.")
        
        return avisos_ativos

    def _carregar_noticias_feed(self) -> List[Dict[str, Any]]:
        """Baixa e processa as notícias do feed RSS."""
        entradas_processadas = []
        try:
            feed = feedparser.parse(URL_FEED)
            # Pega apenas as 6 primeiras entradas
            for entrada in feed.entries[:6]:
                # Extrair imagem da descrição
                url_imagem = None
                sopa = BeautifulSoup(entrada.get('description', ''), 'html.parser')
                tag_img = sopa.find('img')
                if tag_img and tag_img.get('src'):
                    url_imagem = tag_img['src']
                    if url_imagem.startswith(("http://fct.ufg.brhttps:", "https://fct.ufg.brhttps:")):
                        url_imagem = url_imagem.replace("http://fct.ufg.br", "").replace("https://fct.ufg.br", "")
                
                # Limpar texto da descrição
                sopa = BeautifulSoup(entrada.get('description', ''), 'html.parser')
                for script in sopa(["script", "style"]):
                    script.decompose()
                descricao = sopa.get_text(separator=' ', strip=True)
                descricao = ' '.join(descricao.split())
                
                # Truncar textos
                titulo = entrada.get('title', '')[:LIMITE_TITULO]
                
                if len(descricao) > LIMITE_DESCRICAO:
                    ultimo_espaco = descricao.rfind(' ', 0, LIMITE_DESCRICAO)
                    descricao = descricao[:ultimo_espaco] + '...' if ultimo_espaco > 0 else descricao[:LIMITE_DESCRICAO] + '...'
                
                # Capturar e formatar data da notícia
                data_str = entrada.get('published', 'Data não disponível')
                try:
                    data_parsed = time.strptime(data_str, "%a, %d %b %Y %H:%M:%S %z")
                    data_formatada = time.strftime("%d/%m/%Y - %H:%M", data_parsed)
                except (ValueError, TypeError):
                    data_formatada = "Data não disponível"
                
                entrada_processada = {
                    'titulo': titulo,
                    'descricao': descricao,
                    'link': entrada.get('link', ''),
                    'url_imagem': url_imagem,
                    'data': data_formatada,
                    'tipo': 'noticia' # Identificador interno
                }
                entradas_processadas.append(entrada_processada)
        except Exception as e:
            print(f"Erro ao obter notícias do feed: {e}")
        return entradas_processadas

    def run(self):
        """Método principal da thread: carrega avisos e notícias, mistura e emite."""
        avisos = self._carregar_avisos_ativos()
        noticias = self._carregar_noticias_feed()
        
        conteudo_final = avisos + noticias
        
        if not conteudo_final:
            print("Nenhum conteúdo (notícia ou aviso) disponível para exibição.")
            self.conteudo_pronto.emit([])
            return

        # Mistura os itens para uma exibição mais dinâmica
        random.shuffle(conteudo_final)
        
        self.conteudo_pronto.emit(conteudo_final)

# -------------------------------------------------------------
# HELPER PARA CRIAR QR CODE (sem alterações)
# -------------------------------------------------------------
def criar_qr_code(url, tamanho=150):
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        img_pil = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img_pil.save(buffer, format='PNG')
        buffer.seek(0)
        qimagem = QImage.fromData(buffer.getvalue())
        return QPixmap.fromImage(qimagem).scaled(tamanho, tamanho, Qt.AspectRatioMode.KeepAspectRatio)
    except Exception as e:
        print(f"Erro ao criar QR code: {str(e)}")
        return QPixmap()

# -------------------------------------------------------------
# WIDGET PARA EXIBIÇÃO DO CONTEÚDO (CARROSSEL)      
# -------------------------------------------------------------
class CarrosselConteudo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.itens_carrossel = []
        self.indice_atual = 0
        
        self.layout = QVBoxLayout(self)
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; }
            QLabel#titulo { font-size: 28px; font-weight: bold; color: #0072b9; margin-bottom: 5px; }
            QLabel#data { font-size: 16px; color: #555; font-style: italic; margin-bottom: 10px; }
            QLabel#descricao { font-size: 26px; color: #333; margin-bottom: 10px; }
        """)
        
        self.conteiner_conteudo = QWidget()
        self.layout_conteudo = QHBoxLayout(self.conteiner_conteudo)
        
        self.rotulo_imagem = QLabel("Carregando imagem...")
        self.rotulo_imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rotulo_imagem.setFixedSize(LARGURA_IMAGEM, ALTURA_IMAGEM)
        self.rotulo_imagem.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd; border-radius: 10px;")
        
        self.conteiner_texto = QWidget()
        self.layout_texto = QVBoxLayout(self.conteiner_texto)
        
        self.rotulo_titulo = QLabel("Carregando conteúdo...")
        self.rotulo_titulo.setObjectName("titulo")
        self.rotulo_titulo.setWordWrap(True)
        
        self.rotulo_data = QLabel("")
        self.rotulo_data.setObjectName("data")
        self.rotulo_data.setWordWrap(True)
        
        self.rotulo_descricao = QLabel()
        self.rotulo_descricao.setObjectName("descricao")
        self.rotulo_descricao.setWordWrap(True)
        self.rotulo_descricao.setAlignment(Qt.AlignmentFlag.AlignJustify)
        
        self.conteiner_qr = QWidget()
        self.layout_qr = QHBoxLayout(self.conteiner_qr)
        self.layout_qr.setContentsMargins(0, 0, 0, 0)
        
        self.rotulo_qr = QLabel()
        self.rotulo_qr.setFixedSize(150, 150)
        self.layout_qr.addStretch()
        self.layout_qr.addWidget(self.rotulo_qr)
        
        self.layout_texto.addWidget(self.rotulo_titulo)
        self.layout_texto.addWidget(self.rotulo_data)
        self.layout_texto.addWidget(self.rotulo_descricao)
        self.layout_texto.addStretch()
        self.layout_texto.addWidget(self.conteiner_qr)
        
        self.layout_conteudo.addWidget(self.rotulo_imagem)
        self.layout_conteudo.addWidget(self.conteiner_texto, 2)
        self.layout.addWidget(self.conteiner_conteudo)
        
        self.timer_carrossel = QTimer(self)
        self.timer_carrossel.timeout.connect(self.proximo_item)
        
        self.gerenciador_conteudo = GerenciadorConteudo()
        self.gerenciador_conteudo.conteudo_pronto.connect(self.quando_conteudo_pronto)
        self.gerenciador_conteudo.start()
    
    def quando_conteudo_pronto(self, itens):
        self.itens_carrossel = itens
        if itens:
            self.indice_atual = 0
            self.atualizar_exibicao()
            self.timer_carrossel.start(10000)  # Avança para próximo item a cada 10 segundos
        else:
            self.rotulo_titulo.setText("Não foi possível carregar conteúdo.")
            self.rotulo_descricao.setText("Verifique a conexão com a internet e o arquivo de avisos.")
            self.rotulo_data.setText("")
            self.rotulo_imagem.setText("Sem conteúdo")
    
    def atualizar_exibicao(self):
        if not self.itens_carrossel:
            return
        
        item = self.itens_carrossel[self.indice_atual]
        self.rotulo_titulo.setText(item['titulo'])
        self.rotulo_data.setText(item.get('data', ''))
        
        texto_descricao = item['descricao']
        # Adiciona a dica do QR code se a notícia foi truncada
        if item.get('tipo') == 'noticia' and texto_descricao.endswith("..."):
            texto_descricao += " <i>(leia mais no QR Code)</i>"
        self.rotulo_descricao.setText(texto_descricao)
        
        if item.get('link'):
            self.rotulo_qr.setPixmap(criar_qr_code(item['link']))
            self.conteiner_qr.setVisible(True)
        else:
            self.conteiner_qr.setVisible(False)
        
        if item.get('url_imagem'):
            self.baixar_imagem(item['url_imagem'])
        else:
            self.rotulo_imagem.setText("Sem imagem disponível")
            self.rotulo_imagem.setPixmap(QPixmap()) # Limpa pixmap anterior
    
    def baixar_imagem(self, url):
        self.rotulo_imagem.setText("Carregando imagem...")
        try:
            resposta = requests.get(url, timeout=10)
            if resposta.status_code == 200:
                qimagem = QImage.fromData(resposta.content)
                pixmap = QPixmap.fromImage(qimagem)
                
                imagem_pixmap = pixmap.scaled(
                    LARGURA_IMAGEM, ALTURA_IMAGEM,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                fundo = QPixmap(LARGURA_IMAGEM, ALTURA_IMAGEM)
                fundo.fill(QColor("#ffffff"))
                painter = QPainter(fundo)
                x = (LARGURA_IMAGEM - imagem_pixmap.width()) // 2
                y = (ALTURA_IMAGEM - imagem_pixmap.height()) // 2
                painter.drawPixmap(x, y, imagem_pixmap)
                painter.end()
                
                self.rotulo_imagem.setPixmap(fundo)
            else:
                self.rotulo_imagem.setText("Não foi possível carregar a imagem")
        except Exception as e:
            print(f"Erro ao baixar imagem '{url}': {e}")
            self.rotulo_imagem.setText("Erro ao carregar a imagem")
    
    def proximo_item(self):
        if self.itens_carrossel:
            self.indice_atual = (self.indice_atual + 1) % len(self.itens_carrossel)
            self.atualizar_exibicao()
    
    def atualizar_conteudo(self):
        print("Iniciando atualização de conteúdo...")
        # Cria uma nova instância para garantir uma nova busca
        self.gerenciador_conteudo = GerenciadorConteudo()
        self.gerenciador_conteudo.conteudo_pronto.connect(self.quando_conteudo_pronto)
        self.gerenciador_conteudo.start()

# -------------------------------------------------------------
# WIDGET PARA A ANIMAÇÃO DA BOLINHA (sem alterações)
# -------------------------------------------------------------
class BallAnimation(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(200, 200)
        self.dx = 3
        self.dy = 3
        self.timer_move = QTimer(self)
        self.timer_move.timeout.connect(self.update_position)
        self.timer_move.start(5)
        self.toggle_timer = QTimer(self)
        self.toggle_timer.timeout.connect(self.toggle_visibility)
        self.toggle_timer.start(60000)
        self.visible_state = True
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.show()
    
    def toggle_visibility(self):
        self.setVisible(not self.isVisible())
    
    def update_position(self):
        if not self.isVisible(): return
        parent_rect = self.parent().rect()
        new_x = self.x() + self.dx
        new_y = self.y() + self.dy
        if not (0 <= new_x <= parent_rect.width() - self.width()): self.dx = -self.dx
        if not (0 <= new_y <= parent_rect.height() - self.height()): self.dy = -self.dy
        self.move(self.x() + self.dx, self.y() + self.dy)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#0072b9"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())
        fonte = QFont("Arial", 16)
        painter.setFont(fonte)
        painter.setPen(QColor("white"))
        rect_texto_f = QRectF(self.rect().adjusted(10, 10, -10, -10))
        opcao_texto = QTextOption(Qt.AlignmentFlag.AlignCenter)
        opcao_texto.setWrapMode(QTextOption.WrapMode.WordWrap)
        painter.drawText(rect_texto_f, "Olá! Utilize o mouse para interagir com o painel!", opcao_texto)

# -------------------------------------------------------------
# WIDGET PARA O MENU LATERAL (sem alterações)
# -------------------------------------------------------------
class MenuLateral(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QWidget { background-color: #F5F5F5; border-radius: 10px; }
            QPushButton { font-size: 18px; color: #424242; background: transparent; 
                         border: none; padding: 8px; text-align: left; }
            QPushButton:hover { background-color: #E0E0E0; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 20, 5, 20)
        layout.setSpacing(10)
        
        self.botoes = {
            "inicio": QPushButton("🏠  Página Inicial"),
            "campus": QPushButton("🏛️  Conheça o Campus"),
            "onibus": QPushButton("🚌  Linha de Ônibus"),
            "horarios": QPushButton("⏰  Horário de Aulas"),
            "mapa": QPushButton("🗺️  Mapa de Salas"),
            "pessoas": QPushButton("👥  Equipe FCT/UFG"),
            "extensao": QPushButton("🌱  Ações de Extensão")
        }
        
        for btn in self.botoes.values():
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)
        
        layout.addStretch()

# -------------------------------------------------------------
# JANELA PRINCIPAL (com pequenas adaptações)
# -------------------------------------------------------------
class AplicacaoTelaCheia(QMainWindow):
    def __init__(self):
        super().__init__()
        QGuiApplication.instance().installEventFilter(self)
        self.setWindowTitle("Painel Interativo FCT")
        self.showFullScreen()
        self.setMouseTracking(True)
        
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)
        
        # Cabeçalho 
        cabecalho = QWidget()
        cabecalho.setStyleSheet("background-color: #0072b9;")
        layout_cabecalho = QHBoxLayout(cabecalho)
        layout_cabecalho.setContentsMargins(10, 10, 10, 10)
        
        self.btn_hamburger = QPushButton("☰")
        self.btn_hamburger.setFixedSize(40, 40)
        self.btn_hamburger.setStyleSheet("""
            QPushButton { background-color: #0072b9; color: white; border: none; font-size: 24px; }
            QPushButton:hover { background-color: #2096f3; }
        """)
        self.btn_hamburger.clicked.connect(self.alternar_menu)
        layout_cabecalho.addWidget(self.btn_hamburger)
        
        rotulo_titulo = QLabel("Painel Interativo FCT/UFG")
        rotulo_titulo.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        rotulo_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rotulo_titulo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_cabecalho.addWidget(rotulo_titulo)
        
        espaco_direito = QWidget()
        espaco_direito.setFixedSize(40, 40)
        layout_cabecalho.addWidget(espaco_direito)
        
        layout_principal.addWidget(cabecalho)
        
        layout_conteudo = QHBoxLayout()
        layout_conteudo.setContentsMargins(0, 0, 0, 0)
        layout_conteudo.setSpacing(0)
        
        self.menu_lateral = MenuLateral()
        self.menu_visivel = MENU_INICIAL_VISIVEL
        self.menu_lateral.setMaximumWidth(220 if self.menu_visivel else 0)
        layout_conteudo.addWidget(self.menu_lateral)
        
        self.area_conteudo = QStackedWidget()
        self.area_conteudo.setStyleSheet("background-color: #f0f0f0;")
        
        self.carrossel_conteudo = CarrosselConteudo()
        self.webview = QWebEngineView()
        self.webview.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        self.webview.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        
        self.area_conteudo.addWidget(self.carrossel_conteudo)
        self.area_conteudo.addWidget(self.webview)
        self.area_conteudo.setCurrentWidget(self.carrossel_conteudo)
        
        layout_conteudo.addWidget(self.area_conteudo)
        layout_principal.addLayout(layout_conteudo)
        
        self.menu_lateral.botoes["inicio"].clicked.connect(self.mostrar_inicio)
        self.menu_lateral.botoes["campus"].clicked.connect(
            lambda: self.carregar_url("https://prezi.com/view/MZjulFdzyMstq9zoDLVX/"))
        self.menu_lateral.botoes["horarios"].clicked.connect(
            lambda: self.carregar_url("https://ti-fct.github.io/horariosFCT/"))
        self.menu_lateral.botoes["mapa"].clicked.connect(
            lambda: self.carregar_url("https://ti-fct.github.io/Painel-FCT/mapa.html"))        
        self.menu_lateral.botoes["onibus"].clicked.connect(
            lambda: self.carregar_url("https://rmtcgoiania.com.br/index.php/linhas-e-trajetos/area-sul?buscar=555"))
        self.menu_lateral.botoes["pessoas"].clicked.connect(
            lambda: self.carregar_url("https://app.powerbi.com/view?r=eyJrIjoiNjUzMDMzOWUtNzViNS00NGYyLTk1YTYtMWY5MWE5OGI1YzAzIiwidCI6ImIxY2E3YTgxLWFiZjgtNDJlNS05OGM2LWYyZjJhOTMwYmEzNiJ9"))
        self.menu_lateral.botoes["extensao"].clicked.connect(
            lambda: self.carregar_url("https://app.powerbi.com/view?r=eyJrIjoiMDcyZWQ2NWMtZTVkMy00YzMyLTkyYjQtNzFmMjQ1MzVjZDcwIiwidCI6ImIxY2E3YTgxLWFiZjgtNDJlNS05OGM2LWYyZjJhOTMwYmEzNiJ9"))
        
        self.timer_atualizacao = QTimer(self)
        self.timer_atualizacao.timeout.connect(self.atualizar_conteudo)
        self.timer_atualizacao.start(INTERVALO_ATUALIZACAO_CONTEUDO * 1000)
        
        self.timer_inatividade = QTimer(self)
        self.timer_inatividade.setInterval(60000) # 1 minuto
        self.timer_inatividade.timeout.connect(self.voltar_para_home)
        self.timer_inatividade.start()
        
        if ANIMACAO_BOLINHA_ATIVA:
            self.ballAnimation = BallAnimation(self)
            self.ballAnimation.move(10, 10)
        else:
            self.ballAnimation = None

    def alternar_menu(self):
        largura_alvo = 0 if self.menu_visivel else 220
        self.menu_lateral.setMaximumWidth(largura_alvo)
        self.menu_visivel = not self.menu_visivel
    
    def voltar_para_home(self):
        self.mostrar_inicio()
    
    def mostrar_inicio(self):
        self.area_conteudo.setCurrentWidget(self.carrossel_conteudo)
    
    def atualizar_conteudo(self):
        self.carrossel_conteudo.atualizar_conteudo()
    
    def carregar_url(self, url: str):
        self.webview.load(QUrl(url))
        self.area_conteudo.setCurrentWidget(self.webview)
    
    def eventFilter(self, fonte, evento):
        if evento.type() in (QEvent.Type.MouseMove, QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress):
            self.timer_inatividade.start()
            if self.ballAnimation and self.ballAnimation.isVisible():
                self.ballAnimation.hide()
                # O timer da bolinha a fará reaparecer depois
        return super().eventFilter(fonte, evento)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = AplicacaoTelaCheia()
    janela.show()
    sys.exit(app.exec())