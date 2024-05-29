# Использование официального Python образа версии 3.11
FROM python:3.11-alpine

# Установка рабочей директории
WORKDIR /usr/src/app

# Копирование файла зависимостей
COPY requirements.txt .

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остального кода приложения
COPY . .

# Указание команды по умолчанию для запуска bot.py
CMD ["python3", "bot.py"]
