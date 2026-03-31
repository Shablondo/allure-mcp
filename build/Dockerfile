FROM docker-registry.x5.ru/python:3.12.13-trixie

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта для установки пакета
COPY pyproject.toml README.md ./
COPY src ./src

# Устанавливаем пакет вместе с зависимостями
RUN pip config --user set global.index https://art.x5.ru/artifactory/pypi-global-remote
RUN pip config --user set global.trusted-host "art.x5.ru"
RUN pip install --trusted-host art.x5.ru --no-cache-dir .

# Команда для запуска MCP сервера
CMD ["python", "-m", "allure_testops_mcp.server"]
