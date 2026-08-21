#!/usr/bin/env bash
# Установочный скрипт ноды: ставит Xray-core, sing-box, агента и системные сервисы.
#
# Использование:
#   curl -sSL https://panel.example.com/install.sh | bash -s -- --token <AGENT_TOKEN> --panel https://panel.example.com
#
# TODO:
# - определение ОС/архитектуры
# - установка Xray-core (последний релиз)
# - установка sing-box (последний релиз)
# - установка systemd unit для agent.py
# - получение TLS-сертификата через acme.sh/certbot
# - регистрация ноды в панели по токену

set -euo pipefail
echo "TODO: install script"
