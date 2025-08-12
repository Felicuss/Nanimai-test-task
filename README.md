## Balance Service (FastAPI + gRPC)

Минимальный запуск и использование.

### Запуск
```bash
docker compose up -d --build
```

- Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- gRPC: localhost:50051

### Локальная установка и запуск (без Docker)
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker run --name balance-db -e POSTGRES_PASSWORD=password -e POSTGRES_DB=balance -p 5432:5432 -d postgres:17.5
export DB_HOST=localhost DB_PORT=5432 DB_NAME=balance DB_USER=postgres DB_PASSWORD=password
uvicorn app.main:app --host 0.0.0.0 --port 8000
python -m app.grpc.server
```

### REST эндпоинты

— GET `/balance/{user_id}` — получить баланс
- Параметры (path):
  - `user_id` — идентификатор пользователя

— POST `/balance/{user_id}/limits` — изменить максимум баланса
- Параметры (path):
  - `user_id` — идентификатор пользователя
- Тело (JSON):
  - `delta` (int) — на сколько изменить максимум; может быть положительным или отрицательным

— POST `/balance/{user_id}/current` — изменить текущий баланс
- Параметры (path):
  - `user_id` — идентификатор пользователя
- Тело (JSON):
  - `delta` (int) — на сколько изменить текущий баланс; может быть положительным или отрицательным (не допускается уход в минус и превышение максимума с учётом `locked_total`)

— POST `/balance/{user_id}/transactions` — открыть транзакцию (заблокировать средства)
- Параметры (path):
  - `user_id` — идентификатор пользователя
- Тело (JSON):
  - `service_id` (string) — идентификатор сервиса, открывающего транзакцию
  - `external_tx_id` (string) — внешний ID транзакции в вашем сервисе (для идемпотентности)
  - `amount` (int > 0) — сумма к блокировке
  - `timeout_seconds` (int 1..3600) — время жизни блокировки, после которого транзакция будет отменена автоматически

— POST `/balance/{user_id}/transactions/{external_tx_id}/confirm` — подтвердить транзакцию (списать средства)
- Параметры (path):
  - `user_id` — идентификатор пользователя
  - `external_tx_id` — внешний ID транзакции (должен совпадать с открытой)
- Тело (JSON):
  - `service_id` (string) — идентификатор сервиса, открывшего транзакцию (должен совпадать)

— POST `/balance/{user_id}/transactions/{external_tx_id}/cancel` — отменить транзакцию (разблокировать средства)
- Параметры (path):
  - `user_id` — идентификатор пользователя
  - `external_tx_id` — внешний ID транзакции (должен совпадать с открытой)
- Тело (JSON):
  - `service_id` (string) — идентификатор сервиса, открывшего транзакцию (должен совпадать)

— POST `/balance/{user_id}/repair` — восстановление баланса в валидное состояние
- Параметры (path):
  - `user_id` — идентификатор пользователя

### Переменные окружения (опционально)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`


