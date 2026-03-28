# 📊 Expert Monitor

Автоматический мониторинг экспертных прогнозов о глобальных циклах, кризисах и их влиянии на Чехию и Украину.

## Что это делает

Раз в месяц (1-го числа) система автоматически:

1. **Монитор** — обходит ~25 источников (блоги экспертов, think tanks, данные) и собирает свежие публикации
2. **Фильтр** — через Gemini AI отбирает наиболее релевантные материалы, сверяя с базой знаний
3. **Контекст** — анализирует найденное с точки зрения жителя Чехии и владельца квартиры в Украине
4. **Саммари** — генерирует итоговый отчёт на русском языке

Результат: Markdown-отчёт + веб-страница на GitHub Pages.

## Эксперты и источники

- **Рэй Далио** — большие циклы, долговые кризисы
- **Питер Турчин** — клиодинамика, перепроизводство элит
- **Нил Хоув** — теория поколений, «четвёртый поворот»
- **Нассим Талеб** — чёрные лебеди, антихрупкость
- **ITR Economics** — прогноз депрессии 2030-х
- **Think tanks**: WEF, Brookings, RAND, Santa Fe Institute и др.
- **Чехия/ЕС**: ČNB, ECB, Bruegel, IDEA CERGE-EI
- **Украина**: ISW, KSE Institute, VoxUkraine

## ⚡ Быстрая установка (15 минут)

### Шаг 1: Получи бесплатный API-ключ Gemini

1. Зайди на [Google AI Studio](https://aistudio.google.com/apikey)
2. Нажми «Create API Key»
3. Скопируй ключ (он выглядит как `AIzaSy...`)

### Шаг 2: Создай GitHub-репо

1. Зайди на [github.com/new](https://github.com/new)
2. Название: `expert-monitor` (или любое другое)
3. Выбери **Public** (нужен для бесплатных GitHub Actions)
4. Нажми «Create repository»

### Шаг 3: Загрузи файлы

**Вариант А — через браузер (самый простой):**
1. Открой свой новый репо на GitHub
2. Нажми «uploading an existing file»
3. Перетащи ВСЕ файлы из скачанной папки
4. Нажми «Commit changes»
5. Повтори для папок `.github/workflows/`, `data/`, `docs/`, `reports/`

**Вариант Б — через командную строку:**
```bash
git clone https://github.com/ТВОЙ_ЮЗЕРНЕЙМ/expert-monitor.git
cd expert-monitor
# Скопируй все файлы проекта в эту папку
git add -A
git commit -m "Initial commit"
git push
```

### Шаг 4: Добавь API-ключ в секреты

1. В репо на GitHub: **Settings** → **Secrets and variables** → **Actions**
2. Нажми **New repository secret**
3. Name: `GEMINI_API_KEY`
4. Secret: вставь свой ключ
5. Нажми **Add secret**

### Шаг 5: Включи GitHub Pages

1. В репо: **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main`, папка: `/docs`
4. Нажми **Save**

### Шаг 6: Запусти первый раз

1. В репо: вкладка **Actions**
2. Слева выбери «Monthly Expert Monitor»
3. Справа нажми **Run workflow** → **Run workflow**
4. Подожди 3-5 минут — появится зелёная галочка

### Готово! 🎉

- **Отчёт** появится в `reports/latest_report.md`
- **Веб-страница**: `https://ТВОЙ_ЮЗЕРНЕЙМ.github.io/expert-monitor/`
- Следующий автоматический запуск: 1-е число следующего месяца

## Структура проекта

```
expert-monitor/
├── .github/workflows/monthly.yml   # GitHub Actions (автозапуск)
├── data/                           # Промежуточные данные
├── docs/index.html                 # Веб-страница (GitHub Pages)
├── reports/
│   ├── latest_report.md            # Последний отчёт
│   └── archive/                    # Архив отчётов
├── agent_monitor.py                # Агент 1: сбор данных
├── agent_filter.py                 # Агент 2: фильтрация через AI
├── agent_context.py                # Агент 3: контекст ЧР/Украина
├── agent_summary.py                # Агент 4: финальный отчёт
├── config.py                       # Настройки
├── gemini_api.py                   # Обёртка Gemini API
├── knowledge_base.md               # База знаний (тезисы из книг)
├── main.py                         # Оркестратор
├── requirements.txt                # Зависимости Python
└── sources.json                    # Конфигурация источников
```

## Локальный запуск (опционально)

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="твой_ключ"
python main.py
```

Или отдельные агенты:
```bash
python main.py --agent 1   # только мониторинг
python main.py --agent 2   # только фильтрация
```

## Стоимость

**$0/месяц.** Всё бесплатно:
- GitHub Actions: 2000 мин/мес (используем ~5 мин)
- GitHub Pages: бесплатный хостинг
- Gemini Flash: 1500 запросов/день бесплатно (используем ~3-4)

## Настройка

### Добавить новый источник
Отредактируй `sources.json` — добавь RSS-фид или URL для скрапинга.

### Изменить частоту
В `.github/workflows/monthly.yml` измени cron:
- Раз в неделю: `cron: '0 9 * * 1'`
- Раз в месяц: `cron: '0 9 1 * *'` (по умолчанию)

### Переключить модель AI
В `config.py` измени `GEMINI_MODEL`. Другие бесплатные варианты:
- `gemini-2.0-flash` (по умолчанию, быстрый)
- `gemini-2.0-flash-lite` (ещё быстрее, менее точный)
