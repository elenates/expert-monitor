"""
Конфигурация проекта Expert Monitor.
Все настройки в одном месте.
"""
import os

# Gemini API (бесплатный)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# Пути к файлам
SOURCES_FILE = "sources.json"
KNOWLEDGE_BASE_FILE = "knowledge_base.md"
RAW_ITEMS_FILE = "data/raw_items.json"
FILTERED_FILE = "data/filtered.json"
CONTEXT_FILE = "data/context.json"
REPORT_FILE = "reports/latest_report.md"
REPORT_ARCHIVE_DIR = "reports/archive"
DOCS_DIR = "docs"

# Настройки мониторинга
MAX_ITEMS_PER_SOURCE = 10       # максимум статей с одного источника
MAX_AGE_DAYS = 45               # не старше 45 дней (запас для ежемесячного запуска)
REQUEST_TIMEOUT = 15            # таймаут запроса в секундах
REQUEST_DELAY = 1               # пауза между запросами (вежливый скрапинг)

# Gemini: лимиты
GEMINI_MAX_INPUT_TOKENS = 900000  # у Flash 1M, оставляем запас
GEMINI_MAX_OUTPUT_TOKENS = 8192
