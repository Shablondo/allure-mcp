FROM docker-registry.x5.ru/python:3.12.13-trixie

ENV PIP_INDEX_URL=https://art.x5.ru/artifactory/pypi-global-remote
ENV PIP_EXTRA_INDEX_URL=https://art.x5.ru/artifactory/pypi-pytorch-remote
ENV PIP_TRUSTED_HOST=art.x5.ru

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта для установки пакета
COPY pyproject.toml README.md ./
COPY src ./src
COPY requirements.txt .

# Устанавливаем пакет вместе с зависимостями
RUN pip install --upgrade pip && pip install --no-cache-dir .

# Команда для запуска MCP сервера
CMD ["python", "-m", "allure_testops_mcp.server"]
