@echo off
REM painel.bat
REM Script para iniciar o ambiente virtual e executar o painel

REM ============= MELHORIAS PROPOSTAS =============

REM 1. Verificação inicial do Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Erro: Python não encontrado no PATH do sistema
    echo Instale Python 3.9+ e adicione ao PATH
    pause
    exit /b 1
)

REM 2. Tratamento de erros no diretório
echo Entrando na pasta...
cd /d "C:\Painel-FCT" 2>nul
if %ERRORLEVEL% neq 0 (
    echo Erro: Diretório C:\Painel-FCT não encontrado
    pause
    exit /b 1
)

REM 3. Atualização do pip antes das instalações
echo Atualizando pip...
python -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 (
    echo Erro ao atualizar pip
    pause
    exit /b 1
)

REM 4. Controle de versão de dependências explícitas
set DEPENDENCIAS=pyqt6==6.5.0 pyqt6-webengine==6.5.0 beautifulsoup4==4.12.2 qrcode==7.4.2 feedparser==6.0.10 pillow==10.0.0 requests==2.31.0

REM 5. Verificação de ativação do ambiente virtual
:activate_venv
echo Ativando ambiente virtual...
call "%VENV_DIR%\Scripts\activate.bat"
if %ERRORLEVEL% neq 0 (
    echo Falha na ativação do ambiente virtual
    echo Tentando recriar o ambiente...
    rmdir /s /q "%VENV_DIR%"
    python -m venv "%VENV_DIR%"
    goto activate_venv
)

REM 6. Instalação silenciosa de dependências
echo Instalando dependências...
pip install %DEPENDENCIAS% --quiet --disable-pip-version-check
if %ERRORLEVEL% neq 0 (
    echo Erro na instalação de dependências
    pause
    exit /b 1
)

REM 7. Execução segura do aplicativo
echo Iniciando aplicação...
start "" /wait python -Xfrozen_modules=off "%NOME_SCRIPT%"

REM 8. Finalização controlada
echo.
echo Aplicativo finalizado. Pressione qualquer tecla para sair...
pause >nul