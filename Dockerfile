FROM python:3.13

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем только необходимые зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt сначала для лучшего кэширования
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Создаем структуру папок
RUN mkdir -p /app/static/frames

# Запускаем main.py
CMD ["python", "main.py"]