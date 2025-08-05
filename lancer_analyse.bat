@echo off
REM Script de lancement simple pour Lab Manual Analyzer
REM Double-cliquez sur ce fichier pour lancer l'analyse

echo.
echo ===============================================
echo    ANALYSEUR DE MANUELS DE LABORATOIRE
echo ===============================================
echo.

REM Verification de Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    echo.
    echo Veuillez installer Python depuis https://python.org
    echo Assurez-vous de cocher "Add Python to PATH" lors de l'installation
    echo.
    pause
    exit /b 1
)

REM Verification des fichiers necessaires
if not exist "lab_manual_analyzer_organized.py" (
    echo ERREUR: Fichier principal manquant
    echo Assurez-vous d'etre dans le bon dossier
    pause
    exit /b 1
)

if not exist "config.json" (
    echo ERREUR: Fichier de configuration manquant
    echo.
    echo Veuillez d'abord configurer vos cles API:
    echo 1. Executez python setup.py
    echo 2. Remplissez config.json avec vos informations
    echo.
    pause
    exit /b 1
)

REM Verification du dossier manuels
if not exist "manuels" (
    echo Creation du dossier manuels...
    mkdir manuels
)

REM Compter les fichiers PDF
set pdf_count=0
for %%f in (manuels\*.pdf) do set /a pdf_count+=1

if %pdf_count%==0 (
    echo.
    echo AUCUN FICHIER PDF TROUVE dans le dossier manuels\
    echo.
    echo Pour utiliser ce programme:
    echo 1. Placez vos manuels PDF dans le dossier "manuels"
    echo 2. Relancez ce script
    echo.
    echo Le dossier manuels a ete cree pour vous.
    pause
    exit /b 0
)

echo Fichiers PDF detectes: %pdf_count%
echo.

REM Test rapide de la configuration
echo Test de la configuration...
python test_config.py >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERREUR DE CONFIGURATION
    echo Vos cles API ne semblent pas correctes.
    echo.
    echo Veuillez verifier:
    echo - Votre cle API Gemini
    echo - Votre fichier de service account Google Cloud
    echo - Votre processor ID Document AI
    echo.
    pause
    exit /b 1
)

echo Configuration OK
echo.

REM Menu de selection
echo Que souhaitez-vous analyser ?
echo.

set file_num=0
for %%f in (manuels\*.pdf) do (
    set /a file_num+=1
    echo   !file_num!. %%~nf
    set "file!file_num!=%%f"
)

echo.
set /a all_option=!file_num!+1
echo   %all_option%. TOUS LES FICHIERS
echo.

set /p choice="Entrez votre choix (1-%all_option%): "

REM Verification du choix
set "valid_choice=false"
for /l %%i in (1,1,%all_option%) do (
    if "!choice!"=="%%i" set "valid_choice=true"
)

if "!valid_choice!"=="false" (
    echo Choix invalide.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo           DEMARRAGE DE L'ANALYSE
echo ===============================================
echo.

REM Execution basee sur le choix
if "!choice!"=="%all_option%" (
    echo Analyse de TOUS les fichiers PDF...
    echo.
    
    set analysis_count=0
    set success_count=0
    
    for %%f in (manuels\*.pdf) do (
        set /a analysis_count+=1
        echo.
        echo [!analysis_count!/%pdf_count%] Analyse de: %%~nf
        echo ----------------------------------------
        
        python lab_manual_analyzer_organized.py "%%f"
        
        if not errorlevel 1 (
            set /a success_count+=1
            echo    REUSSI: %%~nf
        ) else (
            echo    ECHEC: %%~nf
        )
        
        echo.
    )
    
    echo.
    echo ===============================================
    echo            ANALYSE TERMINEE
    echo ===============================================
    echo.
    echo Fichiers traites: !analysis_count!
    echo Analyses reussies: !success_count!
    echo.
    if !success_count! gtr 0 (
        echo Les syntheses sont disponibles dans:
        echo manuels\syntheses\
    )
    
) else (
    REM Analyse d'un fichier specifique
    setlocal enabledelayedexpansion
    set "selected_file=!file%choice%!"
    
    echo Analyse de: !selected_file!
    echo.
    
    python lab_manual_analyzer_organized.py "!selected_file!"
    
    if not errorlevel 1 (
        echo.
        echo ===============================================
        echo          ANALYSE REUSSIE
        echo ===============================================
        echo.
        echo La synthese est disponible dans:
        echo manuels\syntheses\
        echo.
        echo Fichiers generes:
        for %%f in (manuels\syntheses\*) do echo   - %%~nxf
    ) else (
        echo.
        echo ===============================================
        echo           ANALYSE ECHOUEE
        echo ===============================================
        echo.
        echo Verifiez les logs pour plus de details:
        echo - lab_analysis.log
    )
)

echo.
echo Appuyez sur une touche pour fermer...
pause >nul
