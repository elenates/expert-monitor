# 📊 Expert Monitor

Автоматический сбор экспертных прогнозов о глобальных циклах, кризисах и их влиянии на Чехию и Украину. Саммари делается вручную в Claude для максимальной конкретики.

## Как это работает

### Автоматически (15-го числа каждого месяца):

1. **Агент 1 (Монитор)** — обходит ~30 источников (блоги экспертов, think tanks, данные по Чехии, Украине, Ближнему Востоку) и собирает свежие публикации
2. **Агент 2 (Фильтр)** — через Gemini AI отбирает наиболее релевантные материалы и загружает их полный текст
3. **Подготовка** — формирует файл `docs/for_claude.md` для ручного анализа

### Вручную (5 минут):

1. Скачай `docs/for_claude.md` из репо
2. Открой новый чат в [Claude](https://claude.ai)
3. Прикрепи файл + скопируй промпт из `PROMPT_TEMPLATE.md`
4. Получи саммари и задавай уточняющие вопросы

## Эксперты и источники

**Авторы:** Рэй Далио, Питер Турчин, Нил Хоув, Нассим Талеб, ITR Economics, Адам Туз, Nate Hagens

**Think tanks:** WEF, Brookings, RAND, Santa Fe Institute, Cascade Institute, Niskanen Center и др.

**Чехия/ЕС:** ČNB, ECB, Bruegel, IDEA CERGE-EI

**Украина:** ISW, KSE Institute, VoxUkraine

**Ближний Восток:** Al-Monitor, Crisis Group, IISS, Carnegie MEC

## ⚡ Установка

### 1. API-ключ Gemini (бесплатно)

[Google AI Studio](https://aistudio.google.com/apikey) → Create API Key

### 2. GitHub-репо

Создай публичный репо, загрузи все файлы.

### 3. Секрет

Settings → Secrets → Actions → `GEMINI_API_KEY` → вставь ключ.

### 4. Первый запуск

Actions → Monthly Expert Monitor → Run workflow

1-го числа каждого месяца пайплайн запустится автоматически и создаст GitHub Issue с напоминанием — уведомление придёт на email.

### 5. Саммари

После завершения: скачай `docs/for_claude.md` → новый чат в Claude → прикрепи файл + промпт из `PROMPT_TEMPLATE.md`

## Структура проекта

```
expert-monitor/
├── .github/workflows/monthly.yml   # Автозапуск (1-е число месяца)
├── data/                           # Промежуточные данные
│   ├── raw_items.json              # Все найденные материалы
│   ├── filtered.json               # Отфильтрованные + тексты
│   └── for_claude.md               # Файл для Claude
├── docs/
│   └── for_claude.md               # Копия для скачивания
├── reports/archive/                # Архив (если нужно)
├── agent_monitor.py                # Агент 1: сбор данных
├── agent_filter.py                 # Агент 2: фильтрация + тексты
├── prepare_for_claude.py           # Подготовка файла для Claude
├── config.py                       # Настройки
├── gemini_api.py                   # Обёртка Gemini API
├── knowledge_base.md               # База знаний (тезисы из книг)
├── main.py                         # Оркестратор
├── sources.json                    # Конфигурация источников
├── PROMPT_TEMPLATE.md              # Промпт для Claude
└── requirements.txt                # Зависимости
```

## Настройка

### Добавить источник

Отредактируй `sources.json` — добавь RSS или URL для скрапинга.

### Изменить частоту

В `.github/workflows/monthly.yml` измени cron:
- Раз в неделю: `cron: '0 9 * * 1'`
- Раз в месяц: `cron: '0 9 1 * *'` (по умолчанию)

### Запустить вручную

Actions → Monthly Expert Monitor → Run workflow (в любое время)

## Стоимость

**$0/месяц.** GitHub Actions + Gemini Flash бесплатны. Claude Pro — обычная подписка, один чат в месяц.
