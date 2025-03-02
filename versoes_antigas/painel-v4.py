import sys
import requests
import qrcode
import feedparser
import time

from io import BytesIO
from bs4 import BeautifulSoup
from PyQt6.QtCore import (QUrl, QTimer, Qt, QThread, pyqtSignal, QPropertyAnimation, QEvent)
from PyQt6.QtGui import (QGuiApplication, QPainter, QColor, QPixmap, QImage)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QSizePolicy, QStackedWidget)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

# Configurações da aplicação
MENU_INICIAL_VISIVEL = False
URL_FEED = "https://fct.ufg.br/feed"
LIMITE_TITULO = 90
LIMITE_DESCRICAO = 400
INTERVALO_ATUALIZACAO = 3600  # 1 hora em segundos
LARGURA_IMAGEM = 650
ALTURA_IMAGEM = 750

# -------------------------------------------------------------
# COMPONENTE DE DOWNLOAD DE NOTÍCIAS
# -------------------------------------------------------------
class BaixadorNoticias(QThread):
    noticias_prontas = pyqtSignal(list)
    
    def run(self):
        try:
            feed = feedparser.parse(URL_FEED)
            entradas_processadas = []
            # Pega apenas as 6 primeiras entradas
            for entrada in feed.entries[:6]:
                # Extrair imagem da descrição
                url_imagem = None
                sopa = BeautifulSoup(entrada.get('description', ''), 'html.parser')
                tag_img = sopa.find('img')
                if tag_img and tag_img.get('src'):
                    url_imagem = tag_img['src']
                    # Corrigir URLs malformadas
                    if url_imagem.startswith(("http://fct.ufg.brhttps:", "https://fct.ufg.brhttps:")):
                        url_imagem = url_imagem.replace("http://fct.ufg.br", "").replace("https://fct.ufg.br", "")
                
                # Limpar texto da descrição
                sopa = BeautifulSoup(entrada.get('description', ''), 'html.parser')
                for script in sopa(["script", "style"]):
                    script.decompose()
                descricao = sopa.get_text(separator=' ', strip=True)
                descricao = ' '.join(descricao.split())
                
                # Truncar textos
                titulo = entrada.get('title', '')
                if len(titulo) > LIMITE_TITULO:
                    ultimo_espaco = titulo.rfind(' ', 0, LIMITE_TITULO)
                    if ultimo_espaco > 0:
                        titulo = titulo[:ultimo_espaco] + '...'
                    else:
                        titulo = titulo[:LIMITE_TITULO] + '...'
                
                if len(descricao) > LIMITE_DESCRICAO:
                    ultimo_espaco = descricao.rfind(' ', 0, LIMITE_DESCRICAO)
                    if ultimo_espaco > 0:
                        descricao = descricao[:ultimo_espaco] + '...'
                    else:
                        descricao = descricao[:LIMITE_DESCRICAO] + '...'
                
                # Capturar data da notícia (se disponível)
                data = entrada.get('published', 'Data não disponível')
                # Opcional: formatar a data se necessário, por exemplo:
                # try:
                #     data_parsed = time.strptime(data, "%a, %d %b %Y %H:%M:%S %Z")
                #     data = time.strftime("%d/%m/%Y", data_parsed)
                # except Exception:
                #     pass
                
                entrada_processada = {
                    'titulo': titulo,
                    'descricao': descricao,
                    'link': entrada.get('link', ''),
                    'url_imagem': url_imagem,
                    'data': data
                }
                entradas_processadas.append(entrada_processada)
            self.noticias_prontas.emit(entradas_processadas)
        except Exception as e:
            print(f"Erro ao obter notícias: {str(e)}")
            self.noticias_prontas.emit([])

# -------------------------------------------------------------
# HELPER PARA CRIAR QR CODE
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
# WIDGET PARA EXIBIÇÃO DE NOTÍCIAS (CARROSSEL)
# -------------------------------------------------------------
class CarrosselNoticias(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.entradas_noticias = []
        self.indice_atual = 0
        
        self.layout = QVBoxLayout(self)
        # Atualização do estilo para melhor UX
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; }
            QLabel#titulo { font-size: 28px; font-weight: bold; color: #0072b9; margin-bottom: 5px; }
            QLabel#data { font-size: 16px; color: #555; font-style: italic; margin-bottom: 10px; }
            QLabel#descricao { font-size: 26px; color: #333; margin-bottom: 10px; }
        """)
        
        # Layout principal com imagem e texto
        self.conteiner_noticias = QWidget()
        self.layout_noticias = QHBoxLayout(self.conteiner_noticias)
        
        # Imagem
        self.rotulo_imagem = QLabel("Carregando imagem...")
        self.rotulo_imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rotulo_imagem.setFixedSize(LARGURA_IMAGEM, ALTURA_IMAGEM)
        self.rotulo_imagem.setStyleSheet("background-color: #ffffff; border-radius: 10px; padding: 10px;")
        
        # Textos e QR code
        self.conteiner_texto = QWidget()
        self.layout_texto = QVBoxLayout(self.conteiner_texto)
        
        self.rotulo_titulo = QLabel("Carregando notícias...")
        self.rotulo_titulo.setObjectName("titulo")
        self.rotulo_titulo.setWordWrap(True)
        
        # Novo rótulo para a data
        self.rotulo_data = QLabel("")
        self.rotulo_data.setObjectName("data")
        self.rotulo_data.setWordWrap(True)
        
        self.rotulo_descricao = QLabel()
        self.rotulo_descricao.setObjectName("descricao")
        self.rotulo_descricao.setWordWrap(True)
        self.rotulo_descricao.setAlignment(Qt.AlignmentFlag.AlignJustify)
        
        # Reorganizando o container do QR Code em layout horizontal
        self.conteiner_qr = QWidget()
        self.layout_qr = QHBoxLayout(self.conteiner_qr)
        self.layout_qr.setContentsMargins(0, 0, 0, 0)
        self.layout_qr.setSpacing(10)

        
        self.rotulo_qr = QLabel()
        self.rotulo_qr.setFixedSize(150, 150)
        
        self.layout_qr.addStretch()  # Empurra o QR code para a direita
        self.layout_qr.addWidget(self.rotulo_qr)
        
        # Montagem do layout de texto com data
        self.layout_texto.addWidget(self.rotulo_titulo)
        self.layout_texto.addWidget(self.rotulo_data)
        self.layout_texto.addWidget(self.rotulo_descricao)
        self.layout_texto.addStretch()
        self.layout_texto.addWidget(self.conteiner_qr)
        
        self.layout_noticias.addWidget(self.rotulo_imagem)
        self.layout_noticias.addWidget(self.conteiner_texto, 2)
        self.layout.addWidget(self.conteiner_noticias)
        
        # Timers para alternar as notícias
        self.timer_noticias = QTimer(self)
        self.timer_noticias.timeout.connect(self.proxima_noticia)
        
        # Iniciar download de notícias
        self.baixador_noticias = BaixadorNoticias()
        self.baixador_noticias.noticias_prontas.connect(self.quando_noticias_prontas)
        self.baixador_noticias.start()
    
    def quando_noticias_prontas(self, entradas):
        self.entradas_noticias = entradas
        if entradas:
            self.indice_atual = 0
            self.atualizar_exibicao()
            self.timer_noticias.start(10000)  # Avança para próxima notícia a cada 10 segundos
        else:
            self.rotulo_titulo.setText("Não foi possível carregar as notícias.")
    
    def atualizar_exibicao(self):
        if not self.entradas_noticias:
            return
        
        entrada = self.entradas_noticias[self.indice_atual]
        self.rotulo_titulo.setText(entrada['titulo'])
        self.rotulo_data.setText(entrada.get('data', ''))
        
        # Texto da descrição
        texto_descricao = entrada['descricao']
        if texto_descricao.endswith("..."):
            texto_descricao += " leia mais no QCode abaixo"
        self.rotulo_descricao.setText(texto_descricao)
        
        # QR Code
        if entrada['link']:
            self.rotulo_qr.setPixmap(criar_qr_code(entrada['link']))
            self.conteiner_qr.setVisible(True)
        else:
            self.conteiner_qr.setVisible(False)
        
        # Imagem
        if entrada['url_imagem']:
            self.baixar_imagem(entrada['url_imagem'])
        else:
            self.rotulo_imagem.setText("Sem imagem disponível")
    
    def baixar_imagem(self, url):
        self.rotulo_imagem.setText("Carregando imagem...")
        try:
            resposta = requests.get(url, timeout=10)
            if resposta.status_code == 200:
                qimagem = QImage.fromData(resposta.content)
                pixmap = QPixmap.fromImage(qimagem)
                
                # Escalar mantendo proporção
                imagem_pixmap = pixmap.scaled(
                    LARGURA_IMAGEM, ALTURA_IMAGEM,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Centralizar na área disponível
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
            print(f"Erro ao baixar imagem: {str(e)}")
            self.rotulo_imagem.setText("Erro ao carregar a imagem")
    
    def proxima_noticia(self):
        if self.entradas_noticias:
            self.indice_atual = (self.indice_atual + 1) % len(self.entradas_noticias)
            self.atualizar_exibicao()
    
    def atualizar_noticias(self):
        self.baixador_noticias = BaixadorNoticias()
        self.baixador_noticias.noticias_prontas.connect(self.quando_noticias_prontas)
        self.baixador_noticias.start()

# -------------------------------------------------------------
# WIDGET PARA O MENU LATERAL
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
        
        # Botões do menu
        self.botoes = {
            "inicio": QPushButton("🏠  Página Inicial"),
            "campus": QPushButton("🏛️  Conheça o Campus"),
            "onibus": QPushButton("🚌  Linha de Ônibus"),
            "horarios": QPushButton("⏰  Horário de Aulas"),
            "mapa": QPushButton("🗺️  Mapa de Salas"),
            "pessoas": QPushButton("👥  Equipe FCT/UFG"),
            "extensao": QPushButton("🌱  Ações de Extensão")
        }
        
        # Adicionar botões ao layout
        for btn in self.botoes.values():
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)
        
        layout.addStretch()

# -------------------------------------------------------------
# JANELA PRINCIPAL
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
        
        # Botão hamburger
        self.btn_hamburger = QPushButton("☰")
        self.btn_hamburger.setFixedSize(40, 40)
        self.btn_hamburger.setStyleSheet("""
            QPushButton { background-color: #0072b9; color: white; border: none; font-size: 24px; }
            QPushButton:hover { background-color: #2096f3; }
        """)
        self.btn_hamburger.clicked.connect(self.alternar_menu)
        layout_cabecalho.addWidget(self.btn_hamburger)
        
        # Título centralizado
        rotulo_titulo = QLabel("Painel Interativo FCT/UFG")
        rotulo_titulo.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        rotulo_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rotulo_titulo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_cabecalho.addWidget(rotulo_titulo)
        
        # Espaçador para manter o título centralizado
        espaco_direito = QWidget()
        espaco_direito.setFixedSize(40, 40)
        layout_cabecalho.addWidget(espaco_direito)
        
        layout_principal.addWidget(cabecalho)
        
        # Área de conteúdo: menu lateral e área principal
        layout_conteudo = QHBoxLayout()
        layout_conteudo.setContentsMargins(0, 0, 0, 0)
        layout_conteudo.setSpacing(0)
        
        # Menu lateral
        self.menu_lateral = MenuLateral()
        if MENU_INICIAL_VISIVEL:
            self.menu_lateral.setMaximumWidth(220)
            self.menu_visivel = True
        else:
            self.menu_lateral.setMaximumWidth(0)
            self.menu_visivel = False
        layout_conteudo.addWidget(self.menu_lateral)
        
        # Área de conteúdo usando QStackedWidget
        self.area_conteudo = QStackedWidget()
        self.area_conteudo.setStyleSheet("background-color: #f0f0f0;")
        
        # Widgets da área de conteúdo
        self.carrossel_noticias = CarrosselNoticias()
        self.webview = QWebEngineView()
        self.webview.load(QUrl("about:blank"))
        # Habilita o visualizador de PDF integrado
        settings = self.webview.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        
        self.area_conteudo.addWidget(self.carrossel_noticias)
        self.area_conteudo.addWidget(self.webview)
        self.area_conteudo.setCurrentWidget(self.carrossel_noticias)
        
        layout_conteudo.addWidget(self.area_conteudo)
        layout_principal.addLayout(layout_conteudo)
        
        # Conexão dos botões do menu lateral
        self.menu_lateral.botoes["inicio"].clicked.connect(self.mostrar_noticias)
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
        
        # Timers
        self.timer_atualizacao_noticias = QTimer(self)
        self.timer_atualizacao_noticias.timeout.connect(self.atualizar_noticias)
        self.timer_atualizacao_noticias.start(INTERVALO_ATUALIZACAO * 1000)
        
        # Timer de inatividade (1 minuto)
        self.timer_inatividade = QTimer(self)
        self.timer_inatividade.setInterval(60000)
        self.timer_inatividade.timeout.connect(self.voltar_para_home)
        self.timer_inatividade.start()
    
    def alternar_menu(self):
        valor_inicial = self.menu_lateral.maximumWidth()
        largura_alvo = 0 if self.menu_visivel else 220
        self.animacao = QPropertyAnimation(self.menu_lateral, b"maximumWidth")
        self.animacao.setDuration(300)
        self.animacao.setStartValue(valor_inicial)
        self.animacao.setEndValue(largura_alvo)
        self.animacao.start()
        self.menu_visivel = not self.menu_visivel
    
    def voltar_para_home(self):
        self.mostrar_noticias()
    
    def mostrar_noticias(self):
        self.area_conteudo.setCurrentWidget(self.carrossel_noticias)
    
    def atualizar_noticias(self):
        self.carrossel_noticias.atualizar_noticias()
    
    def carregar_url(self, url: str):
        self.webview.load(QUrl(url))
        self.area_conteudo.setCurrentWidget(self.webview)
    
    def eventFilter(self, fonte, evento):
        if evento.type() in (QEvent.Type.MouseMove, QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress):
            self.timer_inatividade.start()
        return super().eventFilter(fonte, evento)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = AplicacaoTelaCheia()
    janela.show()
    sys.exit(app.exec())
