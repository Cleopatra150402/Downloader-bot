# YouTube Telegram Bot

Telegram-бот для скачивания видео с YouTube и отправки их напрямую в чат, с сохранением метаданных в PostgreSQL и контейнеризацией через Docker.


## Участники проекта:      
- ### Мамедова Гузель        5130202/20202
- ### Хотамов Бободжон       5130202/20202


## Определение проблемы
Пользователям не хватает простого способа быстро получить видео с YouTube прямо в чате Telegram без промежуточного сохранения на диск. Из‑за ограничений платформ и меняющихся ссылок велика вероятность получить недоступный или некорректный контент. Нужен бот, который по ссылке на видео скачает ролик, проверит размер и длительность, а затем отправит его в чат в удобном формате.

## Выработка требований

### Пользовательские истории
- Как пользователь, хочу отправить боту ссылку на YouTube и получить видео прямо в чат, чтобы не сохранять файл локально и не искать конвертеры.
- Как пользователь, хочу получать понятные сообщения об ошибках (файл пустой, превышен лимит 50 MB, длительность более 10 минут), чтобы быстро понять, что исправить.
- Как пользователь, хочу увидеть свою статистику успешных загрузок, чтобы понимать, как часто использую бота.

### Оценка пользователей и хранения
- Ожидаемое число пользователей: 10 000 пользователей в сутки.
- Период хранения информации: не менее 5 лет.

## Разработка архитектуры и детальное проектирование

### Характер нагрузки
За этот пункт отвечал Хотамов Бободжон
- Соотношение R/W: чтение ~85%, запись ~15%.
- Объемы трафика: ~30 000 запросов в сутки, средняя нагрузка 0.35 rps, пики 5–10 rps; передача видео 15–40 MB без долговременного хранения.
- Объем диска: реляционные метаданные и логи, десятки гигабайт при максимумах, обычно меньше.


### Контракты API (команды Telegram) и NFR
За этот пункт отвечала Мамедова Гузель
- Команды:
  - /start: приветствие и подсказки.
  - /help: правила использования и ограничения.
  - /stats: агрегированная статистика по пользователю.
  - Текст с YouTube URL: сценарий загрузки и выдача видео или понятной ошибки.
- Нефункциональные требования:
  - До 2 секунд для 95‑го процентили на текстовые команды.
  - 5–20 секунд типично на подготовку видео до 50 MB.
  - Длительность ≤ 10 минут, размер ≤ 50 MB.

### Схема базы данных и обоснование
Схему разрабатывала Мамедова Гузель
```
CREATE TABLE IF NOT EXISTS downloads (
  id SERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  platform VARCHAR(50) NOT NULL,
  video_url TEXT NOT NULL,
  status VARCHAR(20) DEFAULT 'completed',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_downloads_user_id ON downloads(user_id);
CREATE INDEX IF NOT EXISTS idx_downloads_created_at ON downloads(created_at);
```
- Обоснование: операции insert/select, индексы покрывают выборки по пользователю и времени; масштабирование возможно через репликацию чтения.

### Масштабирование ×10
- Несколько экземпляров бота (горизонтальное масштабирование), балансировка webhook/long polling.
- Пулы соединений (PgBouncer), read‑replica для отчётности.
- Короткоживущие кэши метаданных, ограничение конкуррентных загрузок.
- Централизованные логи и мониторинг, алертинг.

## Кодирование и отладка
Кодированием и отладкой занимались все члены команды
- Архитектура: src/bot (инициализация, handlers), src/services (youtube_downloader, database), src/models (Download), src/config (settings).
- Логи: уровень info/warning/error, поток и файл.
- Ограничения: проверка длительности и размера, альтернативные профили yt‑dlp, отключение кэша, принудительная перезапись, безопасная очистка временных файлов.

## Unit тестирование
Разработкой тестов занималась Мамедова Гузель
- Покрытие: youtube_downloader (успех/пустой файл/слишком большой/ошибки), database (save/get/init, исключения), handlers и bot (регистрация, ответы, ветвления).
- Практики: mock/patch для Telegram API, yt‑dlp, файловой системы, БД‑подключений; проверки очистки ресурсов.
- Запуск:
```
pytest
```

## Интеграционное тестирование
- Сценарий: пользователь → URL YouTube → скачивание с форматами и лимитами → отправка видео в чат → запись completed → /stats.
- Запуск в контейнере:
```
docker compose run --rm bot pytest -v -k "integration"
```

## Сборка и запуск (Docker)
За этот пункт отвечал Хотамов Бободжон

### Предусловия
- Достаточно Docker и bash.

### Файлы контейнеризации

Dockerfile:
```
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "src/main.py"]
```

docker-compose.yml:
```
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: telegram_bot
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 1111
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  bot:
    build: .
    depends_on:
      db:
        condition: service_healthy
    environment:
      DB_HOST: db
      DB_NAME: telegram_bot
      DB_USER: postgres
      DB_PASSWORD: 1111
      DB_PORT: 5432
      BOT_TOKEN: 8277658469:AAEYWH4eb8PkPyxDGO-H7UKe-hatBIFhFZk
      # Понятно, что токен не должен быть в открытом доступе, но это учебный проект

    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

volumes:
  postgres_data:
```

### Команды
- Сборка:
```
docker compose build
```
- Unit тесты:
```
docker compose run --rm bot pytest -v --cov=src --cov-report=term-missing
```
- Интеграционные тесты:
```
docker compose run --rm bot pytest -v -k "integration"
```
- Запуск приложения:
```
docker compose up -d
```
- Логи:
```
docker compose logs -f bot
```
- Остановка:
```
docker compose down
```

## Переменные окружения
- BOT_TOKEN — токен Telegram бота.
- DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT — настройки PostgreSQL.
- MAX_DURATION, MAX_FILE_SIZE — опционально, лимиты длительности и размера.

## Структура проекта
За разработку структуры проекта отвечал Хотамов Бободжон
```
.
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── requirements.txt
├── README.md
├── src/
│   ├── main.py
│   ├── bot/
│   │   ├── bot.py
│   │   └── handlers.py
│   ├── services/
│   │   ├── youtube_downloader.py
│   │   └── database.py
│   ├── models/
│   │   └── download.py
│   └── config/
│       └── settings.py
└── tests/
    ├── test_bot.py
    ├── test_handlers.py
    ├── test_database.py
    └── test_youtube_downloader.py
```

## Детали реализации

### Ограничения контента
- Длительность ≤ 10 минут (проверка перед скачиванием).
- Выбор форматов yt‑dlp с ограничением размера и высоты до 720p.
- Альтернативные профили при неудаче, отключение кэша, перезапись.

### Безопасность и устойчивость
- Безопасная очистка временных файлов.
- Секреты — через переменные окружения, .env не включается в образ.
- Политики перезапуска контейнера, том под данные БД, бэкапы по регламенту.

### База данных
- Инициализация таблицы при старте сервиса.
- Индексы по user_id и created_at.
- Возможность репликации чтения при росте нагрузки.

## Рекомендации по эксплуатации
- Параметризовать лимиты через переменные окружения.
- Централизовать логи и метрики при росте.
- Включить fallback стратегию и повторы при сетевых сбоях.
- Ограничение конкуррентных загрузок и ratelimiting.


## Как воспроизвести
- Установить Docker Desktop.
- В docker-compose.yml задать BOT_TOKEN и пароль БД.
- Сборка и запуск:
```
docker compose up --build -d
```
- Проверка:
  - Отправьте /start и ссылку на YouTube, дождитесь ответа с видео.
- Тесты:
```
docker compose run --rm bot pytest -v --cov=src
```
