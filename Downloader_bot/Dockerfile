FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ ./src/

# Переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Команда запуска
CMD ["python", "src/main.py"]

