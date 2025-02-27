import sys
import re
import requests
import qrcode
import feedparser

from datetime import datetime
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image as PILImage
from PyQt6.QtCore import (QUrl, QTimer, Qt, QThread, pyqtSignal, QPropertyAnimation, QEvent)
from PyQt6.QtGui import (QGuiApplication, QKeySequence, QPainter, QColor, QPixmap, QImage, QFont)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSizePolicy)
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Constantes para o feed de notícias
FEED_URL = "https://fct.ufg.br/feed"
TITLE_LIMIT = 80
DESC_LIMIT = 400
UPDATE_INTERVAL = 3600  # 1 hora em segundos

# Constantes para dimensões de imagem
IMAGE_WIDTH = 500
IMAGE_HEIGHT = 600

# -------------------------------------------------------------
# COMPONENTES DE DOWNLOAD DE NOTÍCIAS E IMAGENS
# -------------------------------------------------------------
class NewsDownloader(QThread):
    news_ready = pyqtSignal(list)
    
    def run(self):
        try:
            feed = feedparser.parse(FEED_URL)
            processed_entries = []
            # Alteração aqui: pegar apenas as 6 primeiras entradas
            for entry in feed.entries[:6]:
                processed_entry = {
                    'title': self.truncate_text(self.clean_text(entry.get('title', '')), TITLE_LIMIT),
                    'description': self.truncate_text(self.clean_text(entry.get('description', '')), DESC_LIMIT),
                    'link': entry.get('link', ''),
                    'image_url': self.extract_image(entry.get('description', ''))
                }
                processed_entries.append(processed_entry)
            self.news_ready.emit(processed_entries)
        except Exception as e:
            print(f"Erro ao obter notícias: {str(e)}")
            self.news_ready.emit([])
    
    def clean_text(self, html_content):
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator=' ', strip=True)
        return re.sub(r'\s+', ' ', text).strip()
    
    def truncate_text(self, text, limit):
        if len(text) <= limit:
            return text
        truncated = text[:limit]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
        return truncated + '...'
    
    def fix_image_url(self, url):
        if url.startswith(("http://fct.ufg.brhttps:", "https://fct.ufg.brhttps:")):
            return url.replace("http://fct.ufg.br", "").replace("https://fct.ufg.br", "")
        return url
    
    def extract_image(self, description):
        soup = BeautifulSoup(description, 'html.parser')
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            return self.fix_image_url(img_tag['src'])
        return None

class ImageDownloader(QThread):
    image_ready = pyqtSignal(QPixmap)
    
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
    
    def run(self):
        try:
            response = requests.get(self.url, timeout=10)
            if response.status_code == 200:
                qimage = QImage.fromData(response.content)
                pixmap = QPixmap.fromImage(qimage)
                self.image_ready.emit(pixmap)
            else:
                self.image_ready.emit(QPixmap())
        except Exception as e:
            print(f"Erro ao baixar imagem: {str(e)}")
            self.image_ready.emit(QPixmap())

def create_qr_code(url, size=150):
    # Cria o QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img_pil = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img_pil.save(buffer, format='PNG')
    buffer.seek(0)
    qimage = QImage.fromData(buffer.getvalue())
    pixmap = QPixmap.fromImage(qimage).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio)
    
    # Sobrepõe o texto "leia mais" no QR code
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    return pixmap

# -------------------------------------------------------------
# WIDGET PARA EXIBIÇÃO DE NOTÍCIAS
# -------------------------------------------------------------
class NewsCarousel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.news_entries = []
        self.current_index = 0
        self.current_image_downloader = None
        
        self.layout = QVBoxLayout(self)
        self.setStyleSheet("""
            QWidget { background-color: #ffffff; }
            QLabel#title { font-size: 26px; font-weight: bold; color: #1a237e; }
            QLabel#desc { font-size: 24px; color: #333; }
        """)
        
        self.news_container = QWidget()
        self.news_layout = QHBoxLayout(self.news_container)
        
        # Container da imagem
        self.image_container = QWidget()
        self.image_layout = QVBoxLayout(self.image_container)
        self.image_label = QLabel("Carregando imagem...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(IMAGE_WIDTH, IMAGE_HEIGHT)
        self.image_label.setStyleSheet("""
            QLabel { background-color: #ffffff; border-radius: 10px; padding: 10px; }
        """)
        self.image_layout.addWidget(self.image_label)
        self.image_layout.addStretch()
        
        # Container do texto (título e descrição)
        self.text_container = QWidget()
        self.text_layout = QVBoxLayout(self.text_container)
        self.title_label = QLabel("Carregando notícias...")
        self.title_label.setObjectName("title")
        self.title_label.setWordWrap(True)
        self.desc_label = QLabel()
        self.desc_label.setObjectName("desc")
        self.desc_label.setWordWrap(True)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignJustify)
        
        self.text_layout.addWidget(self.title_label)
        self.text_layout.addWidget(self.desc_label)
        self.text_layout.addStretch()
        
        # Container do QR code (para o link)
        self.link_container = QWidget()
        self.link_layout = QHBoxLayout(self.link_container)
        self.link_layout.setContentsMargins(0, 0, 0, 0)
        self.link_layout.addStretch()
        self.qr_label = QLabel()
        self.qr_label.setFixedSize(150, 150)
        self.link_layout.addWidget(self.qr_label, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.text_layout.addWidget(self.link_container)
        
        self.news_layout.addWidget(self.image_container)
        self.news_layout.addWidget(self.text_container, 2)
        self.layout.addWidget(self.news_container)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_news)
        
        self.downloader = NewsDownloader()
        self.downloader.news_ready.connect(self.on_news_ready)
        self.downloader.start()
    
    def on_news_ready(self, entries):
        self.news_entries = entries
        if entries:
            self.current_index = 0
            self.update_display()
            self.timer.start(10000)
        else:
            self.title_label.setText("Não foi possível carregar as notícias.")
    
    def update_display(self):
        if not self.news_entries:
            return
        
        entry = self.news_entries[self.current_index]
        self.title_label.setText(entry['title'])
        # Se o texto foi truncado (termina com "..."), adiciona " leia mais" após os "..."
        desc_text = entry['description']
        if desc_text.endswith("..."):
            desc_text += " leia mais no qrcode abaixo."
        self.desc_label.setText(desc_text)
        
        if entry['link']:
            self.qr_label.setPixmap(create_qr_code(entry['link']))
            self.link_container.setVisible(True)
        else:
            self.link_container.setVisible(False)
        
        if entry['image_url']:
            self.image_label.setText("Carregando imagem...")
            if self.current_image_downloader is not None and self.current_image_downloader.isRunning():
                self.current_image_downloader.terminate()
            self.current_image_downloader = ImageDownloader(entry['image_url'])
            self.current_image_downloader.image_ready.connect(self.on_image_ready)
            self.current_image_downloader.start()
        else:
            self.image_label.setText("Sem imagem disponível")
    
    def on_image_ready(self, pixmap):
        if not pixmap.isNull():
            image_pixmap = pixmap.scaled(
                IMAGE_WIDTH, 
                IMAGE_HEIGHT,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            background = QPixmap(IMAGE_WIDTH, IMAGE_HEIGHT)
            background.fill(QColor("#ffffff"))
            painter = QPainter(background)
            x = (IMAGE_WIDTH - image_pixmap.width()) // 2
            y = (IMAGE_HEIGHT - image_pixmap.height()) // 2
            painter.drawPixmap(x, y, image_pixmap)
            painter.end()
            self.image_label.setPixmap(background)
            self.image_label.setScaledContents(False)
        else:
            self.image_label.setText("Não foi possível carregar a imagem")
    
    def next_news(self):
        if self.news_entries:
            self.current_index = (self.current_index + 1) % len(self.news_entries)
            self.update_display()
    
    def refresh_news(self):
        self.downloader = NewsDownloader()
        self.downloader.news_ready.connect(self.on_news_ready)
        self.downloader.start()

# -------------------------------------------------------------
# WIDGET PARA O MENU LATERAL (HAMBURGER)
# -------------------------------------------------------------
class SideMenuWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Removida a largura fixa para permitir a animação
        self.setStyleSheet("""
            QWidget { background-color: #F5F5F5; border-radius: 10px; }
            QLabel#title { font-size: 24px; font-weight: bold; color: #1A237E; margin-bottom: 15px; }
            QLabel#desc { font-size: 18px; color: #424242; line-height: 1.4; margin-bottom: 20px; }
            QPushButton { font-size: 18px; color: #424242; background: transparent; border: none; padding: 8px; text-align: left; }
            QPushButton:hover { background-color: #E0E0E0; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 20, 5, 20)
        layout.setSpacing(10)
        
        self.btn_home = QPushButton("🏠  Página Inicial")
        self.btn_campus = QPushButton("🏛️  Conheça o Campus")
        #self.btn_mapa = QPushButton("🗺️  Mapa de Salas")
        self.btn_onibus = QPushButton("🚌  Linha de Ônibus")
        self.btn_horarios = QPushButton("⏰  Horário de Aulas")
        self.btn_fct_pessoas = QPushButton("👥  Equipe FCT/UFG")
        self.btn_fct_extensao = QPushButton("🌱  Ações de Extensão")
        
        for btn in [self.btn_home, self.btn_campus, #self.btn_mapa,
                    self.btn_onibus, self.btn_horarios, self.btn_fct_pessoas,
                    self.btn_fct_extensao]:
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(btn)
        layout.addStretch()

# -------------------------------------------------------------
# QStackEDWIDGET CUSTOMIZADO PARA GERENCIAR AS PÁGINAS
# -------------------------------------------------------------
class QStackedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.widgets = []
        self.current_index = -1
    
    def addWidget(self, widget):
        if self.widgets:
            self.widgets[self.current_index].setVisible(False)
        self.widgets.append(widget)
        self.layout.addWidget(widget)
        self.current_index = len(self.widgets) - 1
        widget.setVisible(True)
    
    def setCurrentWidget(self, widget):
        if widget in self.widgets:
            if self.current_index >= 0:
                self.widgets[self.current_index].setVisible(False)
            self.current_index = self.widgets.index(widget)
            self.widgets[self.current_index].setVisible(True)

# -------------------------------------------------------------
# JANELA PRINCIPAL
# -------------------------------------------------------------
class FullScreenApp(QMainWindow):
    def __init__(self):
        super().__init__()
        QGuiApplication.instance().installEventFilter(self)
        self.setWindowTitle("Painel Interativo FCT")
        self.showFullScreen()
        self.setMouseTracking(True)

        # Timer de inatividade: 5 minutos (300000 ms)
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setInterval(300000)  # Alterado para 5 minutos
        self.inactivity_timer.timeout.connect(self.auto_close_menu)
        self.inactivity_timer.start()
        
        # Variável para controle do estado do menu (aberto/fechado)
        self.menu_open = False
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Cabeçalho com botão hamburger e título centralizado
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #1976d2;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        self.hamburger_btn = QPushButton("☰")
        self.hamburger_btn.setFixedSize(40, 40)
        self.hamburger_btn.setStyleSheet("""
            QPushButton { background-color: #1976d2; color: white; border: none; font-size: 24px; }
            QPushButton:hover { background-color: #2196f3; }
        """)
        self.hamburger_btn.clicked.connect(self.toggle_menu)
        header_layout.addWidget(self.hamburger_btn)
        
        title_label = QLabel("Painel Interativo FCT/UFG")
        title_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(title_label)
        
        right_spacer = QWidget()
        right_spacer.setFixedSize(40, 40)
        header_layout.addWidget(right_spacer)
        
        main_layout.addWidget(header_widget)
        
        # Área de conteúdo: menu lateral e conteúdo principal
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.side_menu = SideMenuWidget()
        # Inicialmente, o menu é fechado (maximumWidth = 0)
        #self.side_menu.setMaximumWidth(0)
        self.side_menu.setMaximumWidth(220)         # menu aberto no inicio
        self.menu_open = True                       # menu aberto no inicio
        content_layout.addWidget(self.side_menu)
        
        self.content_area = QStackedWidget()
        self.news_carousel = NewsCarousel()
        self.webview = QWebEngineView()
        self.content_area.addWidget(self.news_carousel)
        self.content_area.addWidget(self.webview)
        self.content_area.setCurrentWidget(self.news_carousel)
        
        content_layout.addWidget(self.content_area)
        main_layout.addLayout(content_layout)
        
        # Conexão dos botões do menu lateral
        self.side_menu.btn_home.clicked.connect(self.show_news)
        self.side_menu.btn_campus.clicked.connect(lambda: self.carregar_url("https://prezi.com/view/MZjulFdzyMstq9zoDLVX/"))
        self.side_menu.btn_horarios.clicked.connect(lambda: self.carregar_url("https://ti-fct.github.io/horariosFCT/"))
        #self.side_menu.btn_mapa.clicked.connect(lambda: self.carregar_url("file:///C:/Dev/Painel-FCT/mapa.html"))
        self.side_menu.btn_onibus.clicked.connect(lambda: self.carregar_url("https://rmtcgoiania.com.br/index.php/linhas-e-trajetos/area-sul?buscar=555"))
        self.side_menu.btn_fct_pessoas.clicked.connect(lambda: self.carregar_url("https://app.powerbi.com/view?r=eyJrIjoiNjUzMDMzOWUtNzViNS00NGYyLTk1YTYtMWY5MWE5OGI1YzAzIiwidCI6ImIxY2E3YTgxLWFiZjgtNDJlNS05OGM2LWYyZjJhOTMwYmEzNiJ9"))
        self.side_menu.btn_fct_extensao.clicked.connect(lambda: self.carregar_url("https://app.powerbi.com/view?r=eyJrIjoiMDcyZWQ2NWMtZTVkMy00YzMyLTkyYjQtNzFmMjQ1MzVjZDcwIiwidCI6ImIxY2E3YTgxLWFiZjgtNDJlNS05OGM2LWYyZjJhOTMwYmEzNiJ9"))
        
        self.content_area.setStyleSheet("background-color: #f0f0f0;")
        
        self.news_update_timer = QTimer(self)
        self.news_update_timer.timeout.connect(self.refresh_news)
        self.news_update_timer.start(UPDATE_INTERVAL * 1000)
        
        # Timer de inatividade: 1 minutos
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.setInterval(60000)
        self.inactivity_timer.timeout.connect(self.auto_close_menu)
        self.inactivity_timer.start()
    
    def toggle_menu(self):
        start_value = self.side_menu.maximumWidth()
        target_width = 0 if self.menu_open else 220
        self.animation = QPropertyAnimation(self.side_menu, b"maximumWidth")
        self.animation.setDuration(300)
        self.animation.setStartValue(start_value)
        self.animation.setEndValue(target_width)
        self.animation.start()
        self.menu_open = not self.menu_open
    
    def close_menu(self):
        if self.menu_open:
            self.animation = QPropertyAnimation(self.side_menu, b"maximumWidth")
            self.animation.setDuration(300)
            self.animation.setStartValue(self.side_menu.maximumWidth())
            self.animation.setEndValue(0)
            self.animation.start()
            self.menu_open = False
    
    def auto_close_menu(self):
        #self.close_menu()           # menu aberto no inicio
        self.show_news()
    
    def show_news(self):
        self.content_area.setCurrentWidget(self.news_carousel)
    
    def show_web(self):
        self.content_area.setCurrentWidget(self.webview)
    
    def refresh_news(self):
        self.news_carousel.refresh_news()
    
    def carregar_url(self, url: str):
        self.webview.load(QUrl(url))
        self.show_web()
        self.showFullScreen()
    
    def eventFilter(self, source, event):
        if event.type() in (QEvent.Type.MouseMove, QEvent.Type.KeyPress, QEvent.Type.MouseButtonPress):
            self.inactivity_timer.start()
        return super().eventFilter(source, event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FullScreenApp()
    window.show()
    sys.exit(app.exec())
