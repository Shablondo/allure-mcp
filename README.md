# Allure TestOps MCP Server

MCP-сервер для интеграции с [Allure TestOps](https://qameta.io/allure-testops/). Предоставляет инструменты для работы с тест-кейсами — поиск, создание, обновление, удаление, управление сценариями, тегами, вложениями, комментариями и кастомными полями.

## Что это такое

MCP (Model Context Protocol) сервер позволяет AI-ассистенту (OpenCode, Claude, KiloCode и др.) напрямую взаимодействовать с Allure TestOps API. Вы просите ассистента найти, создать или изменить тест-кейс — и он делает это через данный сервер.

## Быстрый старт

### 1. Установить uv

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Или через Homebrew:
```bash
brew install uv
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
Или скачать установщик с [github.com/astral-sh/uv/releases](https://github.com/astral-sh/uv/releases).

**Проверить:**
```bash
uvx --version
# Должен показать 0.4+
```

### 2. Получить API-токен Allure TestOps

1. Откройте Allure TestOps в браузере
2. Нажмите на аватар → **Profile Settings**
3. Найдите раздел **API Tokens** → **Create new token**
4. Скопируйте токен (показан только один раз)
5. Узнайте ID проекта из URL: `https://<host>/project/123/...` → `123` это ID

### 3. Добавить в OpenCode

В `opencode.json`:

```json
{
  "mcp": {
    "allure-testops": {
      "type": "local",
      "command": [
        "uvx",
        "--from",
        "git+https://github.com/Shablondo/allure-mcp.git",
        "allure-testops-mcp"
      ],
      "environment": {
        "ALLURE_TESTOPS_URL": "https://your-allure-testops.com",
        "ALLURE_TESTOPS_API_TOKEN": "your-api-token",
        "ALLURE_TESTOPS_PROJECT_ID": "123"
      },
      "enabled": true,
      "timeout": 600000
    }
  }
}
```

**Замените:**
- `https://your-allure-testops.com` — URL вашего Allure TestOps
- `your-api-token` — API-токен из шага 2
- `123` — ID проекта из шага 2

Остальные переменные окружения имеют значения по умолчанию и не обязательны (см. [Конфигурация](#конфигурация)).

### 4. Перезапустить OpenCode

Новый конфиг вступит в силу после перезапуска. При первом запуске `uvx` скачает и соберёт пакет (~5 секунд), при последующих — использует кэш (мгновенно).

---

## Запуск без OpenCode

### Напрямую из GitHub

```bash
ALLURE_TESTOPS_URL=https://your-allure-testops.com \
ALLURE_TESTOPS_API_TOKEN=your-api-token \
uvx --from git+https://github.com/Shablondo/allure-mcp.git allure-testops-mcp
```

### Локальная разработка

```bash
git clone https://github.com/Shablondo/allure-mcp.git
cd allure-mcp
ALLURE_TESTOPS_URL=https://... ALLURE_TESTOPS_API_TOKEN=... uv run allure-testops-mcp
```

### Docker (альтернативный способ)

```bash
docker run --rm -i \
  -e ALLURE_TESTOPS_URL=https://... \
  -e ALLURE_TESTOPS_API_TOKEN=... \
  -e ALLURE_TESTOPS_PROJECT_ID=123 \
  ghcr.io/shablondo/allure-mcp:latest
```

---

## Конфигурация

Все переменные окружения (жирным — обязательные):

| Переменная | По умолчанию | Описание |
|---|---|---|
| **`ALLURE_TESTOPS_URL`** | — | URL сервера Allure TestOps |
| **`ALLURE_TESTOPS_API_TOKEN`** | — | API-токен для аутентификации |
| `ALLURE_TESTOPS_PROJECT_ID` | — | ID проекта по умолчанию |
| `ALLURE_TESTOPS_TIMEOUT` | 30 | Таймаут запросов (сек) |
| `ALLURE_TESTOPS_CACHE_TTL` | 300 | Время жизни кэша (сек); 0 = отключить |
| `ALLURE_TESTOPS_RETRY_ATTEMPTS` | 3 | Количество повторных попыток |
| `ALLURE_TESTOPS_NETWORK_RETRY_ATTEMPTS` | 1 | Попыток при сетевых ошибках |
| `ALLURE_TESTOPS_RETRY_DELAY` | 2 | Задержка между попытками (сек) |
| `ALLURE_TESTOPS_CIRCUIT_BREAKER_FAILURES` | 5 | Порог срабатывания Circuit Breaker |
| `ALLURE_TESTOPS_CIRCUIT_BREAKER_TIMEOUT` | 60 | Таймаут восстановления (сек) |
| `ALLURE_TESTOPS_MAX_CONNECTIONS` | 100 | Максимум соединений в пуле |
| `ALLURE_TESTOPS_MAX_KEEPALIVE_CONNECTIONS` | 20 | Keepalive-соединений на хост |

Переменные могут передаваться:
- Через `environment` в OpenCode-конфиге (рекомендуется)
- Через `-e` при запуске Docker
- Через `.env` файл (сервер ищет `.env` в рабочей директории)

---

## Обновление

При использовании `uvx --from git+...` **ничего делать не нужно** — `uvx` сам проверяет свежесть и пересобирает пакет при каждом запуске.

При использовании Docker:
```bash
docker pull ghcr.io/shablondo/allure-mcp:latest
```

---

## Доступные MCP-инструменты

### Тест-кейсы

| Инструмент | Описание |
|---|---|
| `allure_getTestCase` | Получить тест-кейс по ID |
| `allure_getTestCases` | Список тест-кейсов проекта с пагинацией |
| `allure_createTestCase` | Создать тест-кейс |
| `allure_updateTestCase` | Обновить тест-кейс |
| `allure_deleteTestCase` | Удалить тест-кейс |

### Поиск

| Инструмент | Описание |
|---|---|
| `allure_suggestTestCases` | Поиск тест-кейсов по строке запроса |
| `allure_searchTestCases` | Поиск по RQL-запросу |
| `allure_validateSearchQuery` | Валидация RQL-запроса |

**Примеры RQL:**
- `name like '%login%'` — поиск по имени
- `status = 'ACTIVE'` — фильтр по статусу
- `tag = 'smoke'` — фильтр по тегу
- `automated = true` — только автоматизированные

### Сценарии (Steps)

| Инструмент | Описание |
|---|---|
| `allure_getScenario` | Получить сценарий тест-кейса |
| `allure_createScenarioStep` | Создать шаг сценария |
| `allure_updateScenarioStep` | Обновить шаг |
| `allure_deleteScenarioStep` | Удалить шаг |

### Теги

| Инструмент | Описание |
|---|---|
| `allure_getTags` | Получить теги тест-кейса |
| `allure_setTags` | Установить теги (заменяет все) |

### Вложения

| Инструмент | Описание |
|---|---|
| `allure_getAttachments` | Список вложений тест-кейса |
| `allure_uploadAttachment` | Загрузить вложение (multipart/form-data) |
| `allure_uploadAttachmentAndLinkStep` | Загрузить вложение и привязать к шагу |
| `allure_getAttachmentContent` | Получить содержимое вложения |
| `allure_updateAttachment` | Обновить метаданные вложения |
| `allure_updateAttachmentContent` | Обновить содержимое вложения |
| `allure_deleteAttachment` | Удалить вложение |

### Комментарии

| Инструмент | Описание |
|---|---|
| `allure_createComment` | Создать комментарий |

### Кастомные поля

| Инструмент | Описание |
|---|---|
| `allure_getCustomFieldsForTestCase` | Список кастомных полей с допустимыми значениями |
| `allure_updateCustomFields` | Обновить значения кастомных полей |
| `allure_getCustomFieldsForSelection` | Поиск кастомных полей |
| `allure_suggestCustomFieldValues` | Поиск значений кастомного поля по строке |

### Примеры (параметризованные данные)

| Инструмент | Описание |
|---|---|
| `allure_getExamples` | Получить примеры тест-кейса |
| `allure_setExamples` | Установить примеры |
| `allure_renameParameter` | Переименовать параметр |
| `allure_generateNwise` | Сгенерировать N-wise комбинации |

### Обзор

| Инструмент | Описание |
|---|---|
| `allure_getOverview` | Обзорная информация о тест-кейсе |

---

## Устранение неполадок

### uvx не найден / команда не распознана

**Windows:** Перезапустите терминал после установки. Если не помогло — добавьте `%USERPROFILE%\.local\bin` в PATH вручную (System Properties → Environment Variables).

**macOS / Linux:** Перезапустите терминал или добавьте в `.zshrc` / `.bashrc`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Ошибка: не задан ALLURE_TESTOPS_URL

Сервер не видит обязательные переменные окружения. Проверьте, что в OpenCode-конфиге заполнен блок `environment` с `ALLURE_TESTOPS_URL` и `ALLURE_TESTOPS_API_TOKEN`.

### Ошибка аутентификации

1. Проверьте, что API-токен действителен (не истёк)
2. Убедитесь, что токен имеет права на чтение/запись тест-кейсов
3. Проверьте URL сервера — он должен начинаться с `https://`
4. Создайте новый токен, если старый скомпрометирован

### Тест-кейс не найден

1. Проверьте ID тест-кейса
2. Убедитесь, что проект существует и у вас есть к нему доступ
3. Проверьте `ALLURE_TESTOPS_PROJECT_ID`

### Пакет не обновляется (uvx)

```bash
uv cache clean
```

При следующем запуске `uvx` пересоберёт пакет с нуля.

### Docker: контейнер не запускается

```bash
docker logs allure-testops-mcp
docker run --rm -i \
  -e ALLURE_TESTOPS_URL=https://... \
  -e ALLURE_TESTOPS_API_TOKEN=... \
  ghcr.io/shablondo/allure-mcp:latest
```

---

## Особенности

### Производительность
- Connection pooling — до 100 соединений, до 20 keepalive
- HTTP/2 для всех запросов
- In-memory LRU-кэш для GET-запросов (TTL: 300 сек)

### Надёжность
- Retry: 3 попытки с задержкой 2 сек
- Circuit Breaker: защита от каскадных отказов (5 failures → открыт на 60 сек)

### Безопасность
- API-токен передаётся через переменные окружения, не логируется
- HTTPS для всех запросов
- Валидация входных данных через Pydantic
- `.env` и `.env.local` в `.gitignore`

---

## Разработка

```bash
git clone https://github.com/Shablondo/allure-mcp.git
cd allure-mcp
uv sync --group dev
uv run pytest
```

### Структура проекта

```
src/allure_testops_mcp/
├── server.py          # Точка входа MCP-сервера
├── config.py          # Конфигурация (env vars)
├── client.py          # HTTP-клиент (пул, retry, circuit breaker)
└── controllers/       # MCP-инструменты
    ├── test_case_controller.py
    ├── test_case_search_controller.py
    ├── test_case_scenario_controller.py
    ├── test_case_tag_controller.py
    ├── test_case_attachment_controller.py
    ├── test_case_custom_field_controller.py
    ├── test_case_example_controller.py
    ├── test_case_issue_controller.py
    ├── test_case_overview_controller.py
    └── comment_controller.py
```

### Сборка Docker-образа

```bash
docker build -f build/Dockerfile -t allure-testops-mcp:latest .
```
