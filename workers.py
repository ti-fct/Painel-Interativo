# workers.py

import requests
import feedparser
import time
from datetime import datetime
from bs4 import BeautifulSoup
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap

from config import URL_FEED, LIMITE_TITULO, LIMITE_DESCRICAO, URL_AVISOS

class BaixadorNoticias(QThread):
    noticias_prontas = pyqtSignal(list)
    def run(self):
        try:
            feed = feedparser.parse(URL_FEED)
            entradas_processadas = []
            for entrada in feed.entries[:6]:
                sopa = BeautifulSoup(entrada.get('description', ''), 'html.parser')
                tag_img = sopa.find('img')
                url_imagem = tag_img['src'] if tag_img and tag_img.get('src') else None
                if url_imagem and url_imagem.startswith(("http://fct.ufg.brhttps:", "https://fct.ufg.brhttps:")):
                    url_imagem = url_imagem.replace("https://fct.ufg.br", "").replace("http://fct.ufg.br", "")
                [s.decompose() for s in sopa(["script", "style"])]
                descricao = ' '.join(sopa.get_text(separator=' ', strip=True).split())
                titulo = entrada.get('title', 'Sem Título')
                if len(titulo) > LIMITE_TITULO: titulo = titulo[:LIMITE_TITULO].rsplit(' ', 1)[0] + '...'
                if len(descricao) > LIMITE_DESCRICAO: descricao = descricao[:LIMITE_DESCRICAO].rsplit(' ', 1)[0] + '... - '
                data_str = entrada.get('published', 'Data não disponível')
                try:
                    data_obj = time.strptime(data_str, "%a, %d %b %Y %H:%M:%S %z")
                    data_formatada = time.strftime("%d/%m/%Y às %H:%M", data_obj)
                except (ValueError, TypeError): data_formatada = 'Data Indisponível'
                entradas_processadas.append({
                    'type': 'noticia', 'titulo': titulo, 'descricao': descricao, 'link': entrada.get('link', ''),
                    'url_imagem': url_imagem, 'data': data_formatada
                })
            self.noticias_prontas.emit(entradas_processadas)
        except Exception as e:
            print(f"Erro ao obter notícias: {e}"); self.noticias_prontas.emit([])

class BaixadorAvisos(QThread):
    avisos_prontos = pyqtSignal(list)
    def run(self):
        try:
            resposta = requests.get(URL_AVISOS, timeout=10)
            resposta.raise_for_status()
            avisos_api = resposta.json()
            avisos_validos = []
            agora = datetime.now()
            for aviso in avisos_api:
                if not aviso.get('targetScreens'):
                    try:
                        inicio = datetime.strptime(aviso['data_inicio'], '%Y-%m-%d %H:%M')
                        fim = datetime.strptime(aviso['data_fim'], '%Y-%m-%d %H:%M')
                        if inicio <= agora <= fim:
                            avisos_validos.append({
                                'type': 'aviso', 'url_imagem': aviso['url_imagem'],
                                'titulo': aviso.get('titulo', 'Aviso'), 'data_inicio_obj': inicio # Adiciona obj para ordenar
                            })
                    except (ValueError, TypeError, KeyError) as e:
                        print(f"Aviso '{aviso.get('titulo')}' ignorado por dados inválidos: {e}")
            
            avisos_validos.sort(key=lambda x: x['data_inicio_obj'], reverse=True)
            self.avisos_prontos.emit(avisos_validos)
        except Exception as e:
            print(f"Erro ao obter avisos: {e}"); self.avisos_prontos.emit([])

class BaixadorImagem(QThread):
    imagem_pronta = pyqtSignal(QPixmap)
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
    def run(self):
        if not self.url: self.imagem_pronta.emit(QPixmap()); return
        try:
            resposta = requests.get(self.url, timeout=15)
            resposta.raise_for_status()
            img = QImage.fromData(resposta.content)
            self.imagem_pronta.emit(QPixmap.fromImage(img))
        except requests.RequestException as e:
            print(f"Erro ao baixar imagem da URL {self.url}: {e}"); self.imagem_pronta.emit(QPixmap())