@echo off
title ETS2 Mod Manager â€” Build
cd /d "%~dp0"

if not exist "venv\" (
    echo [*] Virtual environment missing. Run run.cmd first or check your setup.
    pause
    exit /b
)

call venv\Scripts\activate.bat

echo [*] Cleaning old build output...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [*] Protecting credentials (Embedding JSON into code)...
python protect_credentials.py

echo [*] Installing requirements...
pip install -r requirements.txt

echo [*] Installing PyInstaller...
pip install pyinstaller

echo [*] Getting CustomTkinter path...
for /f "tokens=*" %%i in ('python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"') do set CTK_PATH=%%i

echo [*] Building executable (Version 3.0.0)...
pyinstaller ^
    --name "ETS2ModManager" ^
    --onedir ^
    --windowed ^
    --icon "%CD%\Manager.ico" ^
    --add-data "%CTK_PATH%;customtkinter" ^
    --add-data "Manager.ico;." ^
    --add-data "Manager.png;." ^
    --add-data "ui\assets;ui\assets" ^
    --add-data "webui;webui" ^
    --add-data "tools;tools" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "google.cloud.firestore" ^
    --hidden-import "firebase_admin" ^
    --hidden-import "grpc._cython.cygrpc" ^
    --clean ^
    --noconfirm ^
    main.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo [*] Finalizing: Copying external files...
    copy "Manager.ico" "dist\ETS2ModManager\Manager.ico" >nul
    copy "Manager.png" "dist\ETS2ModManager\Manager.png" >nul
    if not exist "dist\ETS2ModManager\ui\assets" mkdir "dist\ETS2ModManager\ui\assets"
    xcopy "ui\assets\*.png" "dist\ETS2ModManager\ui\assets\" /Y /I >nul
    if not exist "dist\ETS2ModManager\webui" mkdir "dist\ETS2ModManager\webui"
    xcopy "webui\*" "dist\ETS2ModManager\webui\" /E /Y /I >nul
    if exist "dist\ETS2ModManager\_internal" (
        copy "Manager.ico" "dist\ETS2ModManager\_internal\Manager.ico" >nul
        copy "Manager.png" "dist\ETS2ModManager\_internal\Manager.png" >nul
        if not exist "dist\ETS2ModManager\_internal\ui\assets" mkdir "dist\ETS2ModManager\_internal\ui\assets"
        xcopy "ui\assets\*.png" "dist\ETS2ModManager\_internal\ui\assets\" /Y /I >nul
        if not exist "dist\ETS2ModManager\_internal\webui" mkdir "dist\ETS2ModManager\_internal\webui"
        xcopy "webui\*" "dist\ETS2ModManager\_internal\webui\" /E /Y /I >nul
    )
    echo [OK] Build complete. Output: dist\ETS2ModManager\ETS2ModManager.exe
) else (
    echo [ERROR] Build failed. Review the logs above.
)
pause


