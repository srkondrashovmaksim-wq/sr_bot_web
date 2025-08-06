@echo off
REM — перейти в корень проекта
cd /d C:\sr_bot_web

REM — активировать виртуальное окружение
call venv\Scripts\activate

REM — установить все необходимые переменные среды
set DB_USER=root
set DB_PASSWORD=a647ec150
set DB_HOST=localhost
set DB_PORT=3306
set DB_NAME=sr_bot_db
set SECRET_KEY=1f55fc0d894c523964eb22c5c9a27a501c83fd7234fb9d25188968a6cff90d4e

REM — (опционально) ещё раз убедиться, что зависимости установлены
pip install -r requirements.txt

REM — запуск приложения
python app.py
pause
