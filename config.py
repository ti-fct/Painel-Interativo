# config.py

# --- Configurações da Aplicação ---
ANIMACAO_BOLINHA_ATIVA = True
MODO_TELA_CHEIA = True

# --- Configurações do Feed de Notícias ---
URL_FEED = "https://fct.ufg.br/feed"
LIMITE_TITULO = 80
LIMITE_DESCRICAO = 400
INTERVALO_ATUALIZACAO_NOTICIAS = 1800  # meia hora em segundos
INTERVALO_CARROSSEL = 12  # Tempo em segundos para cada item

# --- Configurações da API de Avisos ---
URL_AVISOS = "http://192.168.0.7:3000/api/avisos"
INTERVALO_ATUALIZACAO_AVISOS = 600 # 10 minutos em segundos

# --- Configurações de Aparência ---
LARGURA_MENU = 250

# --- Configurações de URLs ---
URLS = {
    "campus": "https://prezi.com/view/MZjulFdzyMstq9zoDLVX/",
    "horarios": "https://ti-fct.github.io/horariosFCT/",
    "agenda": "https://calendar.google.com/calendar/embed?src=c_851e8fcd8b81aa4d25fe7044895c1fa3bd8422912a043548c0291dd9a1b28e3f%40group.calendar.google.com&ctz=America%2FSao_Paulo",
    "mapa": "https://ti-fct.github.io/Painel-Interativo/mapa.html",
    "onibus": "https://rmtcgoiania.com.br/index.php/linhas-e-trajetos/area-sul?buscar=555",
    "pessoas": "https://app.powerbi.com/view?r=eyJrIjoiNjUzMDMzOWUtNzViNS00NGYyLTk1YTYtMWY5MWE5OGI1YzAzIiwidCI6ImIxY2E3YTgxLWFiZjgtNDJlNS05OGM2LWYyZjJhOTMwYmEzNiJ9",
    "extensao": "https://app.powerbi.com/view?r=eyJrIjoiMDcyZWQ2NWMtZTVkMy00YzMyLTkyYjQtNzFmMjQ1MzVjZDcwIiwidCI6ImIxY2E3YTgxLWFiZjgtNDJlNS05OGM2LWYyZjJhOTMwYmEzNiJ9"
}