@echo off
cd /d "%~dp0"

echo ============================
echo Atualizando GitHub...
echo ============================

git add -A

for /f "tokens=1-3 delims=/" %%a in ("%date%") do set d=%%c-%%b-%%a
for /f "tokens=1-2 delims=:" %%a in ("%time%") do set t=%%a-%%b
set msg=update %d% %t%

git commit -m "%msg%"

git push

echo ============================
echo Finalizado.
echo ============================
pause
