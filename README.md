# Documentação: Painel Interativo FCT

## Visão Geral

O Painel Interativo FCT é uma aplicação desktop desenvolvida em Python com PyQt6 que exibe notícias e informações úteis da Faculdade de Ciência e Tecnologia (FCT) da Universidade Federal de Goiás (UFG). A aplicação funciona como um painel informativo para estudantes, professores e visitantes, apresentando um carrossel de notícias e acesso a diversas informações institucionais.

**Versão atual:** 4

## Características Principais

- Carrossel de notícias atualizado automaticamente
- Menu lateral para navegação
- Exibição de QR codes para acesso a conteúdo completo
- Retorno automático à tela inicial após período de inatividade
- Visualização de páginas web e documentos PDF integrados
- Interface em tela cheia

## Requisitos

### Dependências

- Python 3.x
- PyQt6
- requests
- qrcode
- feedparser
- BeautifulSoup4
- PyQt6-WebEngine

### Instalação de dependências

```bash
pip install pyqt6 pyqt6-webengine beautifulsoup4 qrcode feedparser pillow requests
```

## Estrutura do Código

O código está organizado em várias classes e componentes principais:

### 1. BaixadorNoticias
Thread responsável por baixar e processar o feed RSS de notícias da FCT.

```python
class BaixadorNoticias(QThread):
    # Sinal emitido quando as notícias estiverem prontas
    noticias_prontas = pyqtSignal(list)
    
    def run(self):
        # Baixa e processa as notícias do feed RSS
```

### 2. CarrosselNoticias
Widget que exibe as notícias em formato de carrossel.

```python
class CarrosselNoticias(QWidget):
    def __init__(self, parent=None):
        # Inicializa componentes visuais
        # ...
    
    def quando_noticias_prontas(self, entradas):
        # Atualiza UI quando novas notícias chegam
        
    def atualizar_exibicao(self):
        # Atualiza o display com a notícia atual
        
    def proxima_noticia(self):
        # Avança para a próxima notícia
```

### 3. MenuLateral
Widget que implementa o menu lateral de navegação.

```python
class MenuLateral(QWidget):
    def __init__(self, parent=None):
        # Inicializa botões e layout
```

### 4. AplicacaoTelaCheia
Janela principal que coordena todos os componentes.

```python
class AplicacaoTelaCheia(QMainWindow):
    def __init__(self):
        # Inicializa componentes e timers
        
    def alternar_menu(self):
        # Mostra/esconde o menu lateral
        
    def voltar_para_home(self):
        # Retorna para a tela inicial após inatividade
```

### 5. Helper para QR Code

```python
def criar_qr_code(url, tamanho=150):
    # Gera QR code para uma URL específica
```

## Configurações

As configurações principais podem ser ajustadas modificando as constantes no início do script:

```python
# Configurações da aplicação
MENU_INICIAL_VISIVEL = False         # Define se o menu lateral é visível no início
URL_FEED = "https://fct.ufg.br/feed" # URL do feed RSS
LIMITE_TITULO = 90                   # Tamanho máximo para títulos
LIMITE_DESCRICAO = 400               # Tamanho máximo para descrições
INTERVALO_ATUALIZACAO = 3600         # Tempo em segundos para atualizar notícias (1h)
LARGURA_IMAGEM = 650                 # Largura das imagens de notícias
ALTURA_IMAGEM = 750                  # Altura das imagens de notícias
```

## Fluxo de Funcionamento

1. A aplicação inicia em tela cheia
2. O carrossel de notícias é carregado e exibido inicialmente
3. As notícias são baixadas da URL de feed configurada
4. A cada 10 segundos, o carrossel avança para a próxima notícia
5. A cada hora, as notícias são atualizadas do feed
6. Após 1 minuto de inatividade, o painel retorna para a tela inicial (carrossel)
7. O usuário pode navegar para diferentes conteúdos através do menu lateral

## Links e Recursos Integrados

O painel dá acesso aos seguintes recursos:

- **Página Inicial**: Carrossel de notícias da FCT
- **Conheça o Campus**: Apresentação Prezi sobre o campus
- **Linha de Ônibus**: Informações sobre transporte público
- **Horário de Aulas**: Consulta aos horários de aula
- **Mapa de Salas**: Mapa interativo do campus
- **Equipe FCT/UFG**: Informações sobre o corpo docente e técnico
- **Ações de Extensão**: Projetos de extensão da FCT

## Personalização

Para personalizar a aplicação, você pode modificar:

- Estilos CSS nos métodos `setStyleSheet()`
- URLs nos handlers de botões
- Propriedades do carrossel, como tempo entre notícias
- Tempo de inatividade antes de voltar para a página inicial

## Modo de Execução

Para iniciar a aplicação, execute o script Python:

```bash
python painel.py
```

## Notas Adicionais

- **IMPORTANTE**: Para usar como painel interativo, a constante `MENU_INICIAL_VISIVEL` deve ser configurada como `False`
- A aplicação usa `QPropertyAnimation` para transições suaves do menu
- As imagens de notícias são baixadas e redimensionadas mantendo a proporção original
- Os QR Codes são gerados dinamicamente para cada notícia

## Requisitos de Hardware

- Monitor ou display compatível com a resolução desejada
- Dispositivo de entrada (mouse/teclado/tela touch) para interação
- Conexão com internet para atualização de notícias e acesso a recursos externos

## Resolução de Problemas

### Problema: Imagens não são exibidas
- Verifique a conexão com a internet
- Verifique se as URLs das imagens no feed estão acessíveis

### Problema: Menu lateral não aparece
- Verifique a configuração `MENU_INICIAL_VISIVEL`
- Teste o botão de hamburger (☰) no canto superior esquerdo

### Problema: Carrossel não avança automaticamente
- Verifique se o feed está sendo carregado corretamente
- Verifique os logs para erros de processamento do feed
