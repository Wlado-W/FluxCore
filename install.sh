#!/usr/bin/env bash
#
# FluxCore Orchestration Panel - One-Line Production Installer
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
  ______ _____  _____   _____  ____  _____  ______ 
 |  ____|  __ \|  __ \ / ____|/ __ \|  __ \|  ____|
 | |__  | |__) | |__) | |    | |  | | |__) | |__   
 |  __| |  _  /|  ___/| |    | |  | |  _  /|  __|  
 | |    | | \ \| |    | |____| |__| | | \ \| |____ 
 |_|    |_|  \_\_|     \_____|\____/|_|  \_\______|
EOF
echo -e "${NC}"
echo -e "${GREEN}Установка панели управления FluxCore v1.0.0${NC}\n"

# 0. Проверка Root-прав
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Ошибка: Запустите скрипт от имени root (sudo ./install.sh)${NC}"
  exit 1
fi

# 1. Принятие EULA
echo -e "${YELLOW}--- ЛИЦЕНЗИОННОЕ СОГЛАШЕНИЕ (EULA) ---${NC}"
echo "Используя FluxCore, вы соглашаетесь с правилами использования,"
echo "запретом декомпиляции/реверс-инжиниринга и условиями автоматической"
echo "проверки лицензии. Панель поставляется 'как есть' (AS IS)."
read -p "Вы принимаете условия EULA? [y/N]: " EULA_ACCEPT
if [[ ! "$EULA_ACCEPT" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Установка отменена. Согласие с EULA обязательно.${NC}"
    exit 1
fi

# 2. Параметры сети
echo -e "\n${YELLOW}--- Настройка параметров сети ---${NC}"
read -p "Введите имя домена или IP сервера [localhost]: " SERVER_DOMAIN
SERVER_DOMAIN=${SERVER_DOMAIN:-localhost}

read -p "Введите порт для Web-интерфейса панели [8000]: " PANEL_PORT
PANEL_PORT=${PANEL_PORT:-8000}

# 3. Обновление пакетов и системные зависимости
echo -e "\n${BLUE}[1/6] Установка системных зависимостей (PostgreSQL, Redis, Nginx, Python3.11)...${NC}"
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip python3-dev \
    postgresql postgresql-contrib redis-server nginx git curl rsync build-essential libpq-dev

# 4. Настройка PostgreSQL
echo -e "\n${BLUE}[2/6] Конфигурация PostgreSQL...${NC}"
DB_NAME="fluxcore_db"
DB_USER="fluxcore_user"
DB_PASS=$(openssl rand -hex 16)

sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER DATABASE $DB_NAME OWNER TO $DB_USER;" 2>/dev/null || true

# 5. Развертывание директории и virtualenv
INSTALL_DIR="/opt/fluxcore"
echo -e "\n${BLUE}[3/6] Подготовка окружения в $INSTALL_DIR...${NC}"

mkdir -p $INSTALL_DIR
# Если скрипт запущен из директории с исходниками — копируем их
if [ -f "./manage.py" ]; then
    rsync -av --exclude='venv' --exclude='.git' ./ $INSTALL_DIR/
fi

cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
else
    pip install django djangorestframework psycopg2-binary celery redis requests drf-spectacular geoip2 -q
fi

# Генерация .env файла
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
cat << EOF > .env
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=$SERVER_DOMAIN,127.0.0.1,localhost
DATABASE_URL=postgres://$DB_USER:$DB_PASS@127.0.0.1:5432/$DB_NAME
REDIS_URL=redis://127.0.0.1:6379/0
FLUXCORE_PORT=$PANEL_PORT
EOF

# 6. Миграции и создание суперпользователя
echo -e "\n${BLUE}[4/6] Применение миграций базы данных...${NC}"
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo -e "\n${YELLOW}--- Создание учетной записи Администратора ---${NC}"
read -p "Имя администратора [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}
read -p "Email администратора [admin@fluxcore.internal]: " ADMIN_EMAIL
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@fluxcore.internal}
read -s -p "Пароль администратора: " ADMIN_PASS
echo ""

python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='$ADMIN_USER').exists():
    User.objects.create_superuser('$ADMIN_USER', '$ADMIN_EMAIL', '$ADMIN_PASS')
"

# 7. Настройка Systemd сервиса
echo -e "\n${BLUE}[5/6] Настройка Systemd сервиса...${NC}"
cat << EOF > /etc/systemd/system/fluxcore.service
[Unit]
Description=FluxCore Orchestration Panel Daemon
After=network.target postgresql.service redis.service

[Service]
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/manage.py runserver 0.0.0.0:$PANEL_PORT
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now fluxcore.service

# 8.SSL сертификаты & Nginx (Опционально)
echo -e "\n${BLUE}[6/6] Настройка Nginx...${NC}"
cat << EOF > /etc/nginx/sites-available/fluxcore
server {
    listen 80;
    server_name $SERVER_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:$PANEL_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias $INSTALL_DIR/staticfiles/;
    }
}
EOF

ln -sf /etc/nginx/sites-available/fluxcore /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

# Выпуск Let's Encrypt через acme.sh при наличии домена
if [ "$SERVER_DOMAIN" != "localhost" ] && [[ ! "$SERVER_DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${YELLOW}Попытка автоматического выпуска SSL-сертификата via acme.sh...${NC}"
    curl https://get.acme.sh | sh -s email=$ADMIN_EMAIL || true
    ~/.acme.sh/acme.sh --issue -d $SERVER_DOMAIN --webroot /var/www/html || true
fi

# Итоговый вывод
echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}      Установка FluxCore успешно завершена!          ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "URL Панели:    ${BLUE}http://$SERVER_DOMAIN:$PANEL_PORT${NC} (или через Nginx: http://$SERVER_DOMAIN)"
echo -e "Логин Admin:   ${YELLOW}$ADMIN_USER${NC}"
echo -e "База данных:   ${YELLOW}$DB_NAME${NC} (User: $DB_USER)"
echo -e "Директория:    ${YELLOW}$INSTALL_DIR${NC}"
echo -e "${GREEN}====================================================${NC}"
