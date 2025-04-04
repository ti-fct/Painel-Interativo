# Painel Interativo FCT/UFG

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt-6.0+-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Versão](https://img.shields.io/badge/Versão-4.1-orange.svg)]()

Um painel interativo desenvolvido para a Faculdade de Ciência e Tecnologia (FCT) da Universidade Federal de Goiás (UFG), exibindo notícias, informações do campus, horários e outros recursos relevantes.

## Funcionalidades

- **Feed de Notícias Automático**: Exibe as últimas notícias da FCT/UFG com rotação automática.
- **Menu Interativo**: Navegação intuitiva por diferentes seções de conteúdo.
- **Integração Web**: Carrega páginas web externas para informações específicas.
- **Códigos QR**: Gera códigos QR para cada notícia, permitindo acesso rápido em dispositivos móveis.
- **Modo Automático**: Retorna à tela inicial após período de inatividade.
- **Animação Interativa**: Inclui uma animação visual para atrair a atenção do usuário (opcional).

## Requisitos

- Python 3.6+
- PyQt6
- QtWebEngine
- Bibliotecas Python:
  - requests
  - qrcode
  - feedparser
  - BeautifulSoup4
  - PyQt6-WebEngine

## Instalação

1. Clone o repositório ou baixe os arquivos do projeto.

2. Instale as dependências:

```bash
pip install pyqt6 pyqt6-webengine requests qrcode feedparser beautifulsoup4
```

3. Execute a aplicação:

```bash
python painel_interativo.py
```

## Configuração

As principais configurações podem ser ajustadas editando as variáveis no início do arquivo:

```python
# Configurações da aplicação
MENU_INICIAL_VISIVEL = True     # Define se o menu lateral aparece aberto inicialmente
ANIMACAO_BOLINHA_ATIVA = False  # Ativa/desativa a animação da bolinha flutuante
URL_FEED = "https://fct.ufg.br/feed"  # URL do feed RSS de notícias
LIMITE_TITULO = 90              # Limite de caracteres para títulos
LIMITE_DESCRICAO = 400          # Limite de caracteres para descrições
INTERVALO_ATUALIZACAO = 3600    # Intervalo de atualização de notícias (em segundos)
LARGURA_IMAGEM = 500            # Largura máxima das imagens
ALTURA_IMAGEM = 600             # Altura máxima das imagens
```

Para usar como painel interativo em modo quiosque, configure `MENU_INICIAL_VISIVEL = False`.

## Estrutura do Projeto

O projeto é organizado em componentes principais:

- **BaixadorNoticias**: Thread para download e processamento de notícias do feed RSS.
- **CarrosselNoticias**: Widget para exibição rotativa das notícias com imagens e QR codes.
- **BallAnimation**: Animação interativa flutuante com mensagem ao usuário.
- **MenuLateral**: Menu de navegação com opções para diferentes seções.
- **AplicacaoTelaCheia**: Janela principal integrando todos os componentes.

## Seções Disponíveis

- **Página Inicial**: Feed de notícias da FCT/UFG
- **Conheça o Campus**: Apresentação sobre o campus
- **Linha de Ônibus**: Informações sobre transporte público
- **Horário de Aulas**: Sistema de consulta aos horários das disciplinas
- **Mapa de Salas**: Visualização das instalações e localização de salas
- **Equipe FCT/UFG**: Informações sobre servidores e colaboradores
- **Ações de Extensão**: Projetos e ações de extensão da faculdade

## Personalização

Para personalizar a aplicação:

- Modifique o estilo CSS interno para alterar a aparência
- Adicione novas seções ao menu editando o dicionário `botoes` na classe `MenuLateral`
- Configure URLs diferentes para as seções na função `__init__` da classe `AplicacaoTelaCheia`

## Modo Quiosque

Para usar em modo quiosque (tela cheia sem interrupções):

1. Configure `MENU_INICIAL_VISIVEL = False`
2. Execute em um ambiente onde o sistema operacional inicie a aplicação automaticamente
3. Opcionalmente, ative `ANIMACAO_BOLINHA_ATIVA = True` para indicar interatividade

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para:

1. Criar um fork do projeto
2. Criar um branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Fazer commit de suas alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Enviar para o branch (`git push origin feature/nova-funcionalidade`)
5. Abrir um Pull Request

## Licenciamento

Este projeto está licenciado sob [GPL v3](LICENSE.md). O uso do PyQt6/Qt6 
está sujeito aos termos da [licença GPL](https://www.gnu.org/licenses/gpl-3.0.html).

## Autor

Desenvolvido pela equipe de TI da FCT/UFG.
