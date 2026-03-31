FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта для установки пакета
COPY pyproject.toml README.md ./
COPY src ./src

# Устанавливаем пакет вместе с зависимостями
RUN pip install --no-cache-dir .

# Команда для запуска MCP сервера
CMD ["python", "-m", "allure_testops_mcp.server"]
