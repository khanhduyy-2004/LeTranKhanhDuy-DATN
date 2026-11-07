#!/usr/bin/env bash
# KDSeaFood – cài đặt tự động cho macOS / Linux
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null || { echo "Chưa cài Python 3: https://www.python.org/downloads/"; exit 1; }
command -v mysql   >/dev/null || { echo "Chưa có lệnh mysql: https://dev.mysql.com/downloads/mysql/8.4.html"; exit 1; }
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip >/dev/null
pip install -r requirements.txt
read -r -s -p "Mật khẩu root MySQL (để trống nếu không có): " DBPASS; echo
if [ -z "$DBPASS" ]; then mysql -u root --default-character-set=utf8mb4 < database/kdseafood.sql
else mysql -u root -p"$DBPASS" --default-character-set=utf8mb4 < database/kdseafood.sql; fi
cat > .env <<ENV
SECRET_KEY=$(python3 -c "import secrets;print(secrets.token_hex(24))")
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=$DBPASS
DB_NAME=kdseafood
FLASK_DEBUG=1
ENV
echo "Xong! Chạy: source venv/bin/activate && python run.py  →  http://127.0.0.1:5000"
