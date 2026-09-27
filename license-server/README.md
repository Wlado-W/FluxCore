# FluxCore License Server — ТОЛЬКО для продавца

⚠️ НЕ включай эту папку в репозиторий, который получают клиенты.
Это отдельный сервис, который держишь только ты, на своей инфраструктуре.

## Запуск

```bash
export LICENSING_PRIVATE_KEY=<твой приватный ключ, из generate_keypair>
export ADMIN_SECRET=<придумай секрет для эндпоинта /v1/revoke>
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8443
```

Рекомендуется держать за nginx с HTTPS-сертификатом (Let's Encrypt).

## Отзыв лицензии (например, обнаружил пиратство)

```bash
curl -X POST https://license.твой-домен.com/v1/revoke \
  -H "Content-Type: application/json" \
  -d '{"license_key": "<ключ>", "admin_secret": "<твой ADMIN_SECRET>"}'
```

После отзыва панель клиента перестанет получать свежие токены при
следующей плановой проверке (по умолчанию раз в 12 часов) и заблокируется
после истечения текущего токена (до 24 часов).
