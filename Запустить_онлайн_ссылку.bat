@echo off
chcp 65001 >nul
title ПрофЭксперт - Онлайн Ссылка
echo ========================================================
echo   ООО «ПрофЭксперт» - Демонстрационная Онлайн Ссылка
echo ========================================================
echo.
echo 1. Запуск сервера...
start /b python server.py
timeout /t 2 >nul
echo.
echo 2. Подключение публичной ссылки (не закрывайте это окно)...
echo.
ssh -o StrictHostKeyChecking=no -R 80:127.0.0.1:8085 nokey@localhost.run
pause
