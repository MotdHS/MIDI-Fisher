@echo off

REM Use PyInstaller to create the executable
pyinstaller --onefile midifisher.py

REM Move the executable to the root directory
move dist\midifisher.exe midifisher.exe

REM Clean up unneeded files and directories created by PyInstaller
rd /s /q build dist
del /q midifisher.spec

echo Build complete - The executable is midifisher.exe