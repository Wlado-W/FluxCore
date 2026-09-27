#!/usr/bin/env bash
#
# Установочный скрипт FluxCore ноды.
# Ставит Xray-core, sing-box и агента (FastAPI-демон), настраивает
# systemd-сервисы и регистрирует ноду в панели.
#
# Использование:
#   curl -sSL https://<panel-host>/install.sh | bash -s -- \
#       --token <AGENT_TOKEN> \
#       --panel https://<panel-host> \
#       [--repo https://github.com/<user>/fluxcore.git] \
#       [--port 62050]
#
# Требования: Debian/Ubuntu с systemd, root-доступ.

set -euo pipefail

# --- Параметры по умолчанию ---------------------------------------------
AGENT_TOKEN=""
PANEL_URL=""
REPO_URL="https://github.com/Wlado-W/FluxCore.git"   # TODO: заменить на реальный репозиторий
AGENT_PORT="62050"
INSTALL_DIR="/opt/fluxcore-agent"
ENV_FILE="/etc/fluxcore-agent/agent.env"

# --- Разбор аргументов ----------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --token) AGENT_TOKEN="$2"; shift 2 ;;
    --panel) PANEL_URL="$2"; shift 2 ;;
    --repo) REPO_URL="$2"; shift 2 ;;
    --port) AGENT_PORT="$2"; shift 2 ;;
    *) echo "Неизвестный аргумент: $1"; exit 1 ;;
  esac
done

if [[ -z "$AGENT_TOKEN" || -z "$PANEL_URL" ]]; then
  echo "Использование: install.sh --token <AGENT_TOKEN> --panel <PANEL_URL> [--repo <REPO_URL>] [--port <PORT>]"
  exit 1
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Скрипт должен быть запущен от root (используй sudo)."
  exit 1
fi

echo "==> Определение ОС и архитектуры"
ARCH_RAW="$(uname -m)"
case "$ARCH_RAW" in
  x86_64) ARCH="64" ; SINGBOX_ARCH="amd64" ;;
  aarch64) ARCH="arm64-v8a" ; SINGBOX_ARCH="arm64" ;;
  *) echo "Неподдерживаемая архитектура: $ARCH_RAW"; exit 1 ;;
esac

if ! command -v apt-get >/dev/null 2>&1; then
  echo "Скрипт поддерживает только Debian/Ubuntu (apt-get не найден)."
  exit 1
fi

echo "==> Установка системных зависимостей"
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
  curl unzip git python3 python3-venv python3-pip ca-certificates

# --- Xray-core -------------------------------------------------------------
echo "==> Установка Xray-core"
XRAY_VERSION="$(curl -sSL https://api.github.com/repos/XTLS/Xray-core/releases/latest | grep -oP '"tag_name":\s*"\K[^"]+')"
XRAY_ZIP="Xray-linux-${ARCH}.zip"
curl -sSL -o /tmp/xray.zip "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/${XRAY_ZIP}"
mkdir -p /usr/local/bin /etc/xray
unzip -o -q /tmp/xray.zip -d /tmp/xray-extracted
install -m 755 /tmp/xray-extracted/xray /usr/local/bin/xray
rm -rf /tmp/xray.zip /tmp/xray-extracted

cat > /etc/systemd/system/xray.service << 'EOF'
[Unit]
Description=Xray Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/xray run -config /etc/xray/config.json
Restart=on-failure
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

# Пустой конфиг-заглушка — агент перезапишет его реальным при первом apply-config
echo '{"log":{"loglevel":"warning"},"inbounds":[],"outbounds":[{"protocol":"freedom","tag":"direct"}]}' > /etc/xray/config.json

# --- sing-box ----------------------------------------------------------------
echo "==> Установка sing-box"
SINGBOX_VERSION="$(curl -sSL https://api.github.com/repos/SagerNet/sing-box/releases/latest | grep -oP '"tag_name":\s*"v\K[^"]+')"
SINGBOX_TAR="sing-box-${SINGBOX_VERSION}-linux-${SINGBOX_ARCH}.tar.gz"
curl -sSL -o /tmp/singbox.tar.gz "https://github.com/SagerNet/sing-box/releases/download/v${SINGBOX_VERSION}/${SINGBOX_TAR}"
mkdir -p /etc/sing-box
tar -xzf /tmp/singbox.tar.gz -C /tmp
install -m 755 "/tmp/sing-box-${SINGBOX_VERSION}-linux-${SINGBOX_ARCH}/sing-box" /usr/local/bin/sing-box
rm -rf /tmp/singbox.tar.gz "/tmp/sing-box-${SINGBOX_VERSION}-linux-${SINGBOX_ARCH}"

cat > /etc/systemd/system/sing-box.service << 'EOF'
[Unit]
Description=sing-box Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/sing-box run -c /etc/sing-box/config.json
Restart=on-failure
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

echo '{"log":{"level":"warn"},"inbounds":[],"outbounds":[{"type":"direct","tag":"direct"}]}' > /etc/sing-box/config.json

# --- Агент --------------------------------------------------------------------
echo "==> Установка агента FluxCore"
rm -rf "$INSTALL_DIR"
git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"

python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install --quiet -r "$INSTALL_DIR/agent/requirements.txt"

mkdir -p /etc/fluxcore-agent
cat > "$ENV_FILE" << EOF
AGENT_TOKEN=${AGENT_TOKEN}
AGENT_LISTEN_HOST=0.0.0.0
AGENT_LISTEN_PORT=${AGENT_PORT}
XRAY_BINARY=/usr/local/bin/xray
XRAY_CONFIG_PATH=/etc/xray/config.json
XRAY_SERVICE_NAME=xray
SINGBOX_BINARY=/usr/local/bin/sing-box
SINGBOX_CONFIG_PATH=/etc/sing-box/config.json
SINGBOX_SERVICE_NAME=sing-box
EOF
chmod 600 "$ENV_FILE"

install -m 644 "$INSTALL_DIR/agent/fluxcore-agent.service" /etc/systemd/system/fluxcore-agent.service
# ExecStart в юните ссылается на /opt/fluxcore-agent/venv — уже совпадает с INSTALL_DIR по умолчанию

echo "==> Запуск сервисов"
systemctl daemon-reload
systemctl enable --now xray.service
systemctl enable --now sing-box.service
systemctl enable --now fluxcore-agent.service

echo "==> Регистрация ноды в панели"
PUBLIC_IP="$(curl -sSL https://api.ipify.org || hostname -I | awk '{print $1}')"
curl -sSL -X POST "${PANEL_URL}/api/agent/nodes/register/" \
  -H "Authorization: Bearer ${AGENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"address\": \"${PUBLIC_IP}\", \"agent_port\": ${AGENT_PORT}}" \
  || echo "Предупреждение: не удалось автоматически зарегистрировать ноду — сделай это вручную в панели."

echo "==> Готово. Агент слушает на порту ${AGENT_PORT}, статус: systemctl status fluxcore-agent"
