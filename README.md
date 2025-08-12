# Painel Interativo FCT/UFG

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt-6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Versão](https://img.shields.io/badge/Versão-5.0-orange.svg)]()

Um painel interativo responsivo desenvolvido para a Faculdade de Ciência e Tecnologia (FCT) da Universidade Federal de Goiás (UFG). Exibe notícias e avisos em tempo real, informações do campus, horários, agenda e outros recursos relevantes.

## Funcionalidades

- **Conteúdo Dinâmico**: Exibe avisos via API e as últimas notícias via Feed RSS, em ordem cronológica.
- **Layout Responsivo**: A interface se adapta a diferentes resoluções e proporções de tela.
- **Menu Interativo**: Navegação intuitiva por diferentes seções de conteúdo.
- **Integração Web**: Carrega páginas web externas para informações como agenda, horários e mapas.
- **Modo Quiosque Automático**: Após 2 minutos de inatividade, o painel retorna à tela inicial e exibe o menu, garantindo que esteja sempre pronto para o próximo usuário.
- **Animação de Interatividade**: Quando inativo, uma animação visual com texto convida o usuário a interagir com o painel.
- **Códigos QR**: Gera códigos QR para cada notícia, permitindo acesso rápido ao conteúdo completo em dispositivos móveis.

## Requisitos

- Python 3.8+
- Bibliotecas listadas no arquivo `requirements.txt`.

## Instalação e Uso

1.  Clone o repositório ou baixe os arquivos do projeto.

2.  Crie e ative um ambiente virtual (recomendado):
    ```bash
    python -m venv venv
    # No Windows
    .\venv\Scripts\Activate.ps1
    # No Linux/macOS
    source venv/bin/activate
    ```

3.  Instale as dependências usando o arquivo `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

4.  Execute a aplicação:
    ```bash
    python main.py
    ```

## Gerar Executável (.EXE)

Para empacotar a aplicação em um único arquivo `.exe` para distribuição em Windows, use o **PyInstaller**. A inclusão do `PyQtWebEngine` requer passos adicionais.

1.  Certifique-se de que o PyInstaller está instalado (`pip install pyinstaller`).

2.  **Execute o comando abaixo no terminal**, com seu ambiente virtual ativado.

    **IMPORTANTE**: Substitua `C:/Caminho/Completo/Para/O/Projeto/venv` pelo caminho absoluto do seu ambiente virtual.

    ```bash
    pyinstaller --name "Painel-Interativo-FCT" --noconsole --icon="caminho/para/seu_icone.ico" --add-data "C:/Caminho/Completo/Para/O/Projeto/venv/Lib/site-packages/PyQt6/Qt6/resources;PyQt6/Qt6/resources" --add-data "C:/Caminho/Completo/Para/O/Projeto/venv/Lib/site-packages/PyQt6/Qt6/translations;PyQt6/Qt6/translations" --hidden-import "PyQt6.QtWebEngineCore" main.py
    ```
    
    **IMPORTANTE**: A opção `--onefile` gera apenas um .exe o que o ideal, mas o Windows detecta como vírus, por isso é recomendado gerar a pasta e compactar, ou gerar o .exe adicionar o arquivo as exceções do Windows.

    ```bash
    pyinstaller --name "Painel-Interativo-FCT" --onefile --windowed --icon="caminho/para/seu_icone.ico" --add-data "C:/Caminho/Completo/Para/O/Projeto/venv/Lib/site-packages/PyQt6/Qt6/resources;PyQt6/Qt6/resources" --add-data "C:/Caminho/Completo/Para/O/Projeto/venv/Lib/site-packages/PyQt6/Qt6/translations;PyQt6/Qt6/translations" --hidden-import "PyQt6.QtWebEngineCore" main.py
    ```

3.  O arquivo `Painel-Interativo-FCT.exe` estará na pasta `dist/`.

**Por que o comando é complexo?** O `PyQtWebEngine` depende de muitos arquivos de recursos externos (dicionários, codecs, etc.). As flags `--add-data` copiam esses arquivos essenciais para dentro do `.exe`, e a flag `--hidden-import` garante que o módulo principal do WebEngine seja incluído.

## Configuração

Todas as principais configurações podem ser ajustadas no arquivo **`config.py`**:

```python
# config.py

# Ativa/desativa a animação da bolinha flutuante
ANIMACAO_BOLINHA_ATIVA = True
# Controla se a aplicação inicia em tela cheia
MODO_TELA_CHEIA = True

# URL do feed RSS de notícias e da API de avisos
URL_FEED = "https://fct.ufg.br/feed"
URL_AVISOS = "http://192.168.0.7:3000/api/avisos"

# Intervalos de atualização (em segundos) e tempo de exibição do carrossel
INTERVALO_ATUALIZACAO_AVISOS = 600
INTERVALO_CARROSSEL = 15

# URLs para os botões do menu
URLS = {
    "campus": "https://...",
    "agenda": "https://...",
    # ...
}
```

## Estrutura do Projeto

O projeto é modularizado para facilitar a manutenção:

- **main.py:** Ponto de entrada da aplicação, cria a janela principal, gerencia os timers e a lógica da animação de inatividade.
- **config.py:** Arquivo centralizado para todas as variáveis de configuração (URLs, timers, etc).
- **ui_components.py:** Contém as classes dos principais widgets da interface, como CarrosselNoticias e MenuLateral.
- **workers.py:** Contém as classes QThread (BaixadorNoticias, BaixadorAvisos) que buscam dados da web em segundo plano para não travar a interface.
- **utils.py:** Funções auxiliares, como a geração de QR Codes.
- **requirements.txt:** Lista de todas as dependências do projeto.

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