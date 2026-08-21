# FluxCore

Панель управления VPN-серверами на Django + DRF, с движками Xray-core/v2core
и sing-box (для TUIC/ShadowTLS/NaiveProxy/AnyTLS).

## Структура

- `apps/` — Django-приложения по предметным областям (core, inbounds,
  outbounds, routing, clients, subscriptions, billing, referrals, resellers,
  monitoring, notifications, telegram_bot, accounts, audit, licensing,
  panel_settings, client_portal)
- `agent/` — отдельный лёгкий демон, устанавливаемый на ноды (не зависит от Django)
- `config/` — настройки Django (settings/base|dev|prod, urls, asgi, celery)
- `templates/`, `static/` — фронтенд панели и тем оформления
- `locale/` — переводы (ru/en)

## Быстрый старт (dev)

```bash
cp .env.example .env
python -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Этапы разработки

1. MVP: Node, Inbound, Client, Group, генератор конфигов, install-скрипт, дашборд, подписки
2. Маршрутизация, outbounds, мониторинг нод, 2FA, аудит-лог, темы
3. Биллинг: платежи, тарифы, промокоды, рефералка
4. Бизнес: Telegram-бот, реселлерка, публичный API, аналитика
5. Отказоустойчивость: HA, Vault, CI/CD агента, deep-links, карта нод
6. Коммерциализация: лицензирование, мультитенантность, документация, white-label
