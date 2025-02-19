# Painel Interativo FCT

Aplicação de painel interativo em tela cheia para exibição de conteúdo web com recursos de overlay e detecção de inatividade.

## Descrição

Este projeto consiste em uma aplicação desktop desenvolvida com PyQt6 que oferece:
- Interface full-screen com navegação web integrada
- Sistema de detecção de inatividade
- Overlay animado com hexágono flutuante
- Botões de navegação para diferentes recursos da FCT

## Funcionalidades Principais

- **Interface em Tela Cheia**
  - Modo full-screen automático
  - Barra de navegação persistente
  - Estilização personalizada

- **Navegação Web**
  - 4 botões para acesso rápido a diferentes URLs
  - Integração com Prezi e Power BI

- **Sistema de Inatividade**
  - Overlay aparece após 5 minutos sem atividade
  - Hexágono animado com mensagem de interação
  - Reinício automático ao detectar movimento do mouse

- **Elementos Visuais**
  - Design moderno com cores institucionais
  - Animações suaves
  - Tipografia clara e legível

## Requisitos e Instalação

### Pré-requisitos
- Python 3.10+
- PyQt6
- PyQt6-WebEngine

```bash
# Instalar dependências
pip install PyQt6 PyQt6-WebEngine
