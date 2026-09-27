#!/usr/bin/env bash
#
# FluxCore Orchestration Panel - One-Line Production Installer
#
# Использование: sudo ./install.sh
#

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/fluxcore"
SERVICE_USER="fluxcore"

trap 'echo -e "\n${RED}Установка прервана ошибкой на строке $LINENO. Ничего не удалялось — можно чинить руками и перезапустить.${NC}"' ERR

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
echo -e "${GREEN}Установка панели управления FluxCore${NC}\n"

# --- 0. Проверка root-прав ---
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Ошибка: запустите скрипт от имени root (sudo ./install.sh)${NC}"
  exit 1
fi

# --- 0.1. Защита от повторного запуска поверх существующей установки ---
# БАГ (в исходной версии скрипта): при повторном запуске .env перезаписывался
# новым случайным DB_PASS/SECRET_KEY, а пароль пользователя PostgreSQL при
# этом НЕ менялся (CREATE USER молча падал через || true) — панель переставала
# подключаться к базе. Теперь вместо тихой порчи рабочей установки — явный отказ.
if [ -f "$INSTALL_DIR/.env" ]; then
    echo -e "${YELLOW}Обнаружена существующая установка в $INSTALL_DIR ($INSTALL_DIR/.env уже существует).${NC}"
    echo "Повторный запуск этого скрипта поверх рабочей установки может рассинхронизировать"
    echo "пароли БД и привести к потере доступа. Для обновления версии панели используйте"
    echo "встроенный механизм обновлений (раздел «Обновления» в панели), а для переноса на"
    echo "новый сервер — резервное копирование/восстановление (раздел «Резервные копии»)."
    read -r -p "Всё равно продолжить и переустановить с нуля? Это НЕ трогает БД, но перезапишет .env, nginx и systemd-юниты [y/N]: " FORCE_REINSTALL
    if [[ ! "$FORCE_REINSTALL" =~ ^[Yy]$ ]]; then
        echo "Установка отменена."
        exit 0
    fi
fi

# --- 1. Согласие с EULA ---
echo -e "${YELLOW}--- ЛИЦЕНЗИОННОЕ СОГЛАШЕНИЕ (EULA) ---${NC}"
# Показываем ТОТ ЖЕ текст, что видит администратор внутри панели (единый
# источник правды — templates/eula.txt), а не отдельно продублированную
# и потенциально расходящуюся копию.
if [ -f "$SCRIPT_DIR/templates/eula.txt" ]; then
    cat "$SCRIPT_DIR/templates/eula.txt"
else
    cat << "EOF"
Используя FluxCore, вы соглашаетесь с правилами использования, запретом
декомпиляции/реверс-инжиниринга и обхода аппаратной привязки лицензии (HWID),
а также с условиями автоматического аннулирования лицензии при обнаружении
модификации кода. Панель поставляется «как есть» (AS IS), без каких-либо
гарантий; правообладатель не несёт ответственности за убытки, связанные с
использованием или невозможностью использования ПО.
EOF
fi
echo ""
read -r -p "Вы принимаете условия EULA? [y/N]: " EULA_ACCEPT
if [[ ! "$EULA_ACCEPT" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Установка отменена. Согласие с EULA обязательно.${NC}"
    exit 1
fi

# --- 2. Параметры сети ---
echo -e "\n${YELLOW}--- Настройка параметров сети ---${NC}"
read -r -p "Введите имя домена или IP сервера [localhost]: " SERVER_DOMAIN
SERVER_DOMAIN=${SERVER_DOMAIN:-localhost}

while true; do
    read -r -p "Введите порт для Web-интерфейса панели [8000]: " PANEL_PORT
    PANEL_PORT=${PANEL_PORT:-8000}
    if [[ "$PANEL_PORT" =~ ^[0-9]+$ ]] && [ "$PANEL_PORT" -ge 1 ] && [ "$PANEL_PORT" -le 65535 ]; then
        break
    fi
    echo -e "${RED}Порт должен быть числом от 1 до 65535.${NC}"
done

IS_DOMAIN=false
if [ "$SERVER_DOMAIN" != "localhost" ] && [[ ! "$SERVER_DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    IS_DOMAIN=true
fi

# --- 2.1. Параметры сервера лицензий (необязательно на этом шаге) ---
echo -e "\n${YELLOW}--- Сервер лицензий продавца (можно пропустить и настроить позже через /license/) ---${NC}"
read -r -p "LICENSE_SERVER_URL (например https://license.example.com), Enter — пропустить: " LICENSE_SERVER_URL
read -r -p "LICENSING_PUBLIC_KEY (публичный ключ продавца), Enter — пропустить: " LICENSING_PUBLIC_KEY

# --- 3. Проверка версии Python (требуется 3.11+) ---
echo -e "\n${BLUE}[1/8] Проверка версии Python...${NC}"
PYTHON_BIN="python3"
PY_VERSION_OK=false
if command -v python3 >/dev/null 2>&1; then
    PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info[0])')
    PY_MINOR=$(python3 -c 'import sys; print(sys.version_info[1])')
    if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 11 ]; then
        PY_VERSION_OK=true
    fi
fi

if [ "$PY_VERSION_OK" = false ]; then
    echo -e "${YELLOW}Системный python3 старше 3.11 (или не найден). Пробую установить python3.11 из deadsnakes PPA...${NC}"
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update -qq
        apt-get install -y -qq software-properties-common
        add-apt-repository -y ppa:deadsnakes/ppa >/dev/null 2>&1 || true
        apt-get update -qq
        if apt-get install -y -qq python3.11 python3.11-venv python3.11-dev; then
            PYTHON_BIN="python3.11"
            PY_VERSION_OK=true
        fi
    fi
fi

if [ "$PY_VERSION_OK" = false ]; then
    echo -e "${RED}Не удалось получить Python 3.11+ автоматически. Установите его вручную и запустите скрипт снова.${NC}"
    exit 1
fi
echo "Используется: $($PYTHON_BIN --version)"

# --- 4. Установка системных зависимостей ---
echo -e "\n${BLUE}[2/8] Установка системных зависимостей (PostgreSQL, Redis, Nginx, сборка)...${NC}"
apt-get update -qq
apt-get install -y -qq \
    python3-pip \
    postgresql postgresql-contrib redis-server nginx \
    git curl rsync socat cron build-essential libpq-dev openssl \
    "${PYTHON_BIN}-venv" "${PYTHON_BIN}-dev"

systemctl enable --now postgresql redis-server

# Ждём готовности PostgreSQL — сразу после apt install сокет может быть
# ещё не поднят на медленных/виртуализированных хостах.
for i in $(seq 1 30); do
    if sudo -u postgres pg_isready >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# --- 5. Настройка PostgreSQL ---
echo -e "\n${BLUE}[3/8] Конфигурация PostgreSQL...${NC}"
DB_NAME="fluxcore_db"
DB_USER="fluxcore_user"
DB_PASS=$(openssl rand -hex 16)

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
# Синхронизируем пароль безусловно (а не только при создании) — иначе при
# повторном запуске .env и реальный пароль в PostgreSQL расходятся.
sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER DATABASE $DB_NAME OWNER TO $DB_USER;"

# --- 6. Системный пользователь для сервиса (не root!) ---
echo -e "\n${BLUE}[4/8] Создание системного пользователя $SERVICE_USER...${NC}"
if ! id "$SERVICE_USER" >/dev/null 2>&1; then
    useradd --system --create-home --home-dir "$INSTALL_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
fi

# --- 7. Развёртывание директории и virtualenv ---
echo -e "\n${BLUE}[5/8] Подготовка окружения в $INSTALL_DIR...${NC}"
mkdir -p "$INSTALL_DIR"
if [ -f "$SCRIPT_DIR/manage.py" ]; then
    rsync -a --exclude='venv' --exclude='.git' --exclude='__pycache__' "$SCRIPT_DIR"/ "$INSTALL_DIR"/
fi

cd "$INSTALL_DIR"
"$PYTHON_BIN" -m venv venv
# shellcheck disable=SC1091
source venv/bin/activate
pip install --upgrade pip -q

# БАГ (в исходной версии скрипта): проверялся несуществующий "requirements.txt"
# в корне — реальные файлы лежат в requirements/{base,prod,dev}.txt, поэтому
# всегда срабатывал куцый fallback-список пакетов, без большей части
# реальных зависимостей проекта (channels, celery-beat, cryptography и т.д.).
if [ -f "requirements/prod.txt" ]; then
    pip install -r requirements/prod.txt -q
elif [ -f "requirements/base.txt" ]; then
    pip install -r requirements/base.txt -q
    pip install "uvicorn[standard]>=0.30" "gunicorn>=22.0" -q
else
    echo -e "${RED}Не найден requirements/prod.txt или requirements/base.txt рядом со скриптом.${NC}"
    exit 1
fi

# Генерация .env (имена переменных должны СОВПАДАТЬ с тем, что реально
# читает config/settings/base.py — раньше здесь были DATABASE_URL и
# SECRET_KEY, которые Django ни разу не читает, отчего панель после
# установки не могла подключиться к БД и работала на дефолтном ключе).
SECRET_KEY=$("$PYTHON_BIN" -c "import secrets; print(secrets.token_urlsafe(50))")
{
    echo "DJANGO_SETTINGS_MODULE=config.settings.prod"
    echo "DJANGO_DEBUG=False"
    echo "DJANGO_SECRET_KEY=$SECRET_KEY"
    echo "ALLOWED_HOSTS=$SERVER_DOMAIN,127.0.0.1,localhost"
    echo "POSTGRES_DB=$DB_NAME"
    echo "POSTGRES_USER=$DB_USER"
    echo "POSTGRES_PASSWORD=$DB_PASS"
    echo "POSTGRES_HOST=127.0.0.1"
    echo "POSTGRES_PORT=5432"
    echo "REDIS_URL=redis://127.0.0.1:6379/0"
    echo "FLUXCORE_VERSION=1.0.0"
    if [ -n "$LICENSE_SERVER_URL" ]; then echo "LICENSE_SERVER_URL=$LICENSE_SERVER_URL"; fi
    if [ -n "$LICENSING_PUBLIC_KEY" ]; then echo "LICENSING_PUBLIC_KEY=$LICENSING_PUBLIC_KEY"; fi
} > .env
chmod 600 .env

# --- 8. Миграции ---
echo -e "\n${BLUE}[6/8] Применение миграций базы данных...${NC}"
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py migrate --noinput
python manage.py collectstatic --noinput -v0

# --- 9. Создание администратора ---
echo -e "\n${YELLOW}--- Создание учётной записи администратора ---${NC}"
read -r -p "Имя администратора [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}
read -r -p "Email администратора [admin@fluxcore.internal]: " ADMIN_EMAIL
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@fluxcore.internal}

while true; do
    read -r -s -p "Пароль администратора (минимум 10 символов): " ADMIN_PASS
    echo ""
    read -r -s -p "Повторите пароль: " ADMIN_PASS_CONFIRM
    echo ""
    if [ "$ADMIN_PASS" != "$ADMIN_PASS_CONFIRM" ]; then
        echo -e "${RED}Пароли не совпадают, попробуйте ещё раз.${NC}"
        continue
    fi
    if [ "${#ADMIN_PASS}" -lt 10 ]; then
        echo -e "${RED}Пароль слишком короткий (минимум 10 символов).${NC}"
        continue
    fi
    break
done

# БАГ (в исходной версии скрипта): логин/email/пароль подставлялись прямо в
# строку Python-кода через "$VAR" — символ ' в пароле сломал бы строку и мог
# привести к выполнению произвольного кода. Передаём через переменные
# окружения, а не через интерполяцию в исходный код.
FLUXCORE_ADMIN_USER="$ADMIN_USER" FLUXCORE_ADMIN_EMAIL="$ADMIN_EMAIL" FLUXCORE_ADMIN_PASS="$ADMIN_PASS" \
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ['FLUXCORE_ADMIN_USER']
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, os.environ['FLUXCORE_ADMIN_EMAIL'], os.environ['FLUXCORE_ADMIN_PASS'])
    User.objects.filter(username=username).update(role=User.Role.ADMIN)
    print('Администратор создан.')
else:
    print('Пользователь с таким именем уже существует — пропускаю создание.')
"
unset ADMIN_PASS ADMIN_PASS_CONFIRM

chown -R "$SERVICE_USER":"$SERVICE_USER" "$INSTALL_DIR"

# --- 10. Systemd-юниты: панель (ASGI/uvicorn — не runserver!), Celery worker, Celery beat ---
echo -e "\n${BLUE}[7/8] Настройка systemd-сервисов...${NC}"

# БАГ (в исходной версии скрипта): панель запускалась через `manage.py
# runserver` от имени root. runserver не предназначен для продакшена и не
# обслуживает WebSocket в этом режиме (а у панели есть live-статус нод через
# Channels/ASGI) — и, что важнее, весь процесс, включая код автообновления,
# исполняющий подписанные с сервера лицензий скрипты, работал бы с правами
# root. Теперь: uvicorn (ASGI, уже есть в зависимостях), от имени
# непривилегированного пользователя fluxcore.
cat << SERVICEEOF > /etc/systemd/system/fluxcore.service
[Unit]
Description=FluxCore Orchestration Panel (ASGI)
After=network.target postgresql.service redis-server.service

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
Environment=DJANGO_SETTINGS_MODULE=config.settings.prod
ExecStart=$INSTALL_DIR/venv/bin/uvicorn config.asgi:application --host 0.0.0.0 --port $PANEL_PORT --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Celery worker — без него не работают: обновления/патчи (блок 1), health-
# check и GeoIP нод (блок 4), создание/восстановление бэкапов (блок 5).
cat << SERVICEEOF > /etc/systemd/system/fluxcore-celery.service
[Unit]
Description=FluxCore Celery Worker
After=network.target redis-server.service postgresql.service

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
Environment=DJANGO_SETTINGS_MODULE=config.settings.prod
ExecStart=$INSTALL_DIR/venv/bin/celery -A config worker --loglevel=info
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Celery beat — без него не работает периодическая проверка токена лицензии
# каждые 12 часов (см. CELERY_BEAT_SCHEDULE в settings) и была вообще
# упущена в исходной версии скрипта.
cat << SERVICEEOF > /etc/systemd/system/fluxcore-celerybeat.service
[Unit]
Description=FluxCore Celery Beat
After=network.target redis-server.service postgresql.service

[Service]
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
Environment=DJANGO_SETTINGS_MODULE=config.settings.prod
ExecStart=$INSTALL_DIR/venv/bin/celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Узкое sudo-правило: сервисному пользователю разрешено перезапускать ТОЛЬКО
# сам fluxcore.service без пароля (нужно для функции самообновления, блок 1),
# и ничего больше — не sudo whole system, а один конкретный юнит.
cat << SUDOEOF > /etc/sudoers.d/fluxcore-restart
$SERVICE_USER ALL=(root) NOPASSWD: /usr/bin/systemctl restart fluxcore.service
SUDOEOF
chmod 440 /etc/sudoers.d/fluxcore-restart

systemctl daemon-reload
systemctl enable --now fluxcore.service fluxcore-celery.service fluxcore-celerybeat.service

# --- 11. Nginx + SSL ---
echo -e "\n${BLUE}[8/8] Настройка Nginx и SSL...${NC}"

WEBROOT="/var/www/fluxcore-acme"
mkdir -p "$WEBROOT"

# Промежуточный конфиг на 80 порту — нужен ДО выпуска сертификата, чтобы
# acme.sh мог пройти HTTP-01 challenge через webroot.
cat << NGINXEOF > /etc/nginx/sites-available/fluxcore
server {
    listen 80;
    server_name $SERVER_DOMAIN;

    location /.well-known/acme-challenge/ {
        root $WEBROOT;
    }

    location / {
        proxy_pass http://127.0.0.1:$PANEL_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias $INSTALL_DIR/staticfiles/;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/fluxcore /etc/nginx/sites-enabled/fluxcore
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

SSL_READY=false
CERT_PATH=""
KEY_PATH=""

if [ "$IS_DOMAIN" = true ]; then
    # БАГ (в исходной версии скрипта): сертификат выпускался через acme.sh,
    # но webroot-путь никогда не обслуживался nginx (challenge гарантированно
    # проваливался), а даже если бы прошёл — nginx так и остался бы слушать
    # только 80 порт: выпущенный сертификат никуда не подключался.
    echo -e "${YELLOW}Домен указан — пробую выпустить сертификат Let's Encrypt через acme.sh...${NC}"
    if [ ! -d "$HOME/.acme.sh" ]; then
        curl -s https://get.acme.sh | sh -s email="$ADMIN_EMAIL" || true
    fi
    ACME_SH="$HOME/.acme.sh/acme.sh"
    if [ -x "$ACME_SH" ] && "$ACME_SH" --issue -d "$SERVER_DOMAIN" --webroot "$WEBROOT"; then
        mkdir -p /etc/fluxcore/ssl
        "$ACME_SH" --install-cert -d "$SERVER_DOMAIN" \
            --key-file       /etc/fluxcore/ssl/privkey.pem \
            --fullchain-file /etc/fluxcore/ssl/fullchain.pem \
            --reloadcmd      "systemctl reload nginx" || true
        if [ -f /etc/fluxcore/ssl/fullchain.pem ]; then
            CERT_PATH="/etc/fluxcore/ssl/fullchain.pem"
            KEY_PATH="/etc/fluxcore/ssl/privkey.pem"
            SSL_READY=true
        fi
    fi
    if [ "$SSL_READY" = false ]; then
        echo -e "${YELLOW}Не удалось выпустить сертификат Let's Encrypt (например, домен ещё не указывает на этот сервер). Панель останется на HTTP по порту 80/$PANEL_PORT — перевыпустить сертификат можно позже вручную через acme.sh.${NC}"
    fi
else
    # Самоподписанный сертификат для доступа по IP/localhost — Let's Encrypt
    # сертификаты на голый IP не выпускаются в принципе.
    echo -e "${YELLOW}Домен не указан — генерирую самоподписанный сертификат для доступа по IP...${NC}"
    mkdir -p /etc/fluxcore/ssl
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
        -keyout /etc/fluxcore/ssl/privkey.pem \
        -out /etc/fluxcore/ssl/fullchain.pem \
        -subj "/CN=$SERVER_DOMAIN" >/dev/null 2>&1
    CERT_PATH="/etc/fluxcore/ssl/fullchain.pem"
    KEY_PATH="/etc/fluxcore/ssl/privkey.pem"
    SSL_READY=true
fi

if [ "$SSL_READY" = true ]; then
    cat << NGINXEOF > /etc/nginx/sites-available/fluxcore
server {
    listen 80;
    server_name $SERVER_DOMAIN;
    location /.well-known/acme-challenge/ { root $WEBROOT; }
    location / { return 301 https://\$host\$request_uri; }
}

server {
    listen 443 ssl;
    server_name $SERVER_DOMAIN;

    ssl_certificate     $CERT_PATH;
    ssl_certificate_key $KEY_PATH;

    location / {
        proxy_pass http://127.0.0.1:$PANEL_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static/ {
        alias $INSTALL_DIR/staticfiles/;
    }
}
NGINXEOF
    nginx -t && systemctl restart nginx
fi

# --- Итоговый вывод ---
PROTO="http"
if [ "$SSL_READY" = true ]; then
    PROTO="https"
fi

echo -e "\n${GREEN}====================================================${NC}"
echo -e "${GREEN}      Установка FluxCore успешно завершена!          ${NC}"
echo -e "${GREEN}====================================================${NC}"
echo -e "URL панели:      ${BLUE}${PROTO}://$SERVER_DOMAIN${NC}"
echo -e "Логин admin:     ${YELLOW}$ADMIN_USER${NC}"
echo -e "База данных:     ${YELLOW}$DB_NAME${NC} (user: $DB_USER, пароль сохранён в $INSTALL_DIR/.env)"
echo -e "Директория:      ${YELLOW}$INSTALL_DIR${NC}"
echo -e "Сервис-пользователь: ${YELLOW}$SERVICE_USER${NC} (панель больше не работает от root)"
echo -e "SSL:             $([ "$SSL_READY" = true ] && echo -e "${GREEN}включён ($PROTO)${NC}" || echo -e "${YELLOW}не настроен, работает по HTTP${NC}")"
if [ -z "$LICENSE_SERVER_URL" ] || [ -z "$LICENSING_PUBLIC_KEY" ]; then
    echo -e "${YELLOW}Лицензия ещё не настроена — зайдите в ${PROTO}://$SERVER_DOMAIN/license/ и активируйте лицензию, полученную от продавца.${NC}"
fi
echo -e "${GREEN}====================================================${NC}"
