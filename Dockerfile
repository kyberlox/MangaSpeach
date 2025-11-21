FROM python:3.13

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt сначала для лучшего кэширования
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Запускаем main.py
CMD ["python", "main.py"]