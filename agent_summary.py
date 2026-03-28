"""
Агент 4: Саммари.
Генерирует финальный отчёт на русском языке в формате Markdown.
"""
import json
from datetime import datetime
from pathlib import Path

import config
from gemini_api import call_gemini


SYSTEM_PROMPT = """Ты — автор аналитического дайджеста для русскоязычного человека, 
живущего в Чехии и владеющего квартирой в Украине.

Твой отчёт должен быть:
- Написан простым языком, без академического жаргона
- Практичным — с конкретными рекомендациями «что делать»
- Структурированным — с чёткими секциями
- Честным — если эксперты расходятся во мнениях, укажи это
- На РУССКОМ языке

Формат отчёта — чистый Markdown, готовый к публикации.
Не используй JSON, только Markdown."""


def run_summary() -> str:
    """Генерирует финальный отчёт."""
    print("\n" + "=" * 60)
    print("АГЕНТ 4: САММАРИ")
    print("=" * 60)

    # Загружаем все данные
    filtered_items = []
    context_data = {}

    if Path(config.FILTERED_FILE).exists():
        with open(config.FILTERED_FILE, "r", encoding="utf-8") as f:
            filtered_items = json.load(f)

    if Path(config.CONTEXT_FILE).exists():
        with open(config.CONTEXT_FILE, "r", encoding="utf-8") as f:
            context_data = json.load(f)

    if not filtered_items and not context_data:
        print("  [!] Нет данных для отчёта.")
        return ""

    # Загружаем базу знаний
    kb_path = Path(config.KNOWLEDGE_BASE_FILE)
    knowledge_excerpt = ""
    if kb_path.exists():
        full_kb = kb_path.read_text(encoding="utf-8")
        if "## ОБЩАЯ КАРТИНА" in full_kb:
            knowledge_excerpt = full_kb[full_kb.index("## ОБЩАЯ КАРТИНА"):]

    # Топ материалы для списка источников
    top_items = ""
    for item in filtered_items[:15]:
        top_items += (
            f"- [{item['title']}]({item['url']}) "
            f"({item['source']}, релевантность: {item.get('relevance_score', '?')}/10)\n"
        )

    today = datetime.now().strftime("%Y-%m-%d")
    month_year = datetime.now().strftime("%B %Y")

    prompt = f"""## Данные для отчёта

### Дата: {today}

### Общая картина (база знаний экспертов):
{knowledge_excerpt}

### Контекст Чехии и Украины (анализ Агента 3):
{json.dumps(context_data, ensure_ascii=False, indent=2)}

### Топ материалов за период:
{top_items}

## Задание

Напиши аналитический отчёт в формате Markdown. Структура:

# 📊 Дайджест экспертных прогнозов — {month_year}

## 🌍 Что говорят эксперты: главное за месяц
(2-3 абзаца: ключевые мысли из найденных материалов, как они соотносятся с прогнозами из базы знаний)

## 📈 Где мы сейчас на «большом цикле»
(Оценка текущей позиции по моделям Далио, Турчина, Хоува. Подтвердились ли прогнозы? Что нового?)

## 🇨🇿 Что это значит для Чехии
(Конкретика: крона, недвижимость, работа, энергия. 
Что изменилось за месяц, на что обратить внимание)

## 🇺🇦 Украина: перспективы и риски
(Война, экономика, недвижимость, восстановление. 
Конкретные рекомендации для владельца квартиры)

## 🛡️ Что делать простому человеку
(5-7 конкретных рекомендаций на основе ВСЕХ экспертов. 
Разбить на: «сейчас», «в ближайший год», «на горизонте 5 лет»)

## 📚 Источники
(Список материалов с ссылками)

---
*Отчёт сгенерирован автоматически на основе мониторинга {len(filtered_items)} источников.*

ВАЖНО: пиши отчёт целиком в Markdown. Не используй JSON. 
Будь конкретным, приводи цифры и даты. 
Если данных по какому-то разделу мало — честно укажи это."""

    print("  📤 Генерируем финальный отчёт...")
    report = call_gemini(prompt, system_instruction=SYSTEM_PROMPT)

    if not report:
        print("  [!] Пустой отчёт от Gemini.")
        return ""

    # Сохраняем отчёт
    Path(config.REPORT_ARCHIVE_DIR).mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(exist_ok=True)

    # Основной файл
    with open(config.REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    # Архивная копия
    archive_name = f"report_{today}.md"
    archive_path = Path(config.REPORT_ARCHIVE_DIR) / archive_name
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(report)

    # Обновляем docs/index.html для GitHub Pages
    generate_html_page(report, today)

    print(f"  ✅ Отчёт сохранён: {config.REPORT_FILE}")
    print(f"  📁 Архив: {archive_path}")
    print(f"  🌐 Веб-страница: {config.DOCS_DIR}/index.html")

    return report


def generate_html_page(markdown_content: str, date: str):
    """Генерирует простую HTML-страницу для GitHub Pages."""
    Path(config.DOCS_DIR).mkdir(exist_ok=True)

    # Простая конвертация MD → HTML (без зависимостей)
    html_body = markdown_content
    # Базовые замены
    import re
    # Заголовки
    html_body = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
    # Жирный и курсив
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
    html_body = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_body)
    # Ссылки
    html_body = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" target="_blank">\1</a>', html_body)
    # Списки
    html_body = re.sub(r'^- (.+)$', r'<li>\1</li>', html_body, flags=re.MULTILINE)
    # Параграфы
    html_body = re.sub(r'\n\n', '</p><p>', html_body)
    html_body = f'<p>{html_body}</p>'
    # Горизонтальные линии
    html_body = html_body.replace('<p>---</p>', '<hr>')

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Дайджест экспертных прогнозов</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7;
            color: #1a1a2e;
            background: #f8f9fa;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}
        h1 {{ font-size: 1.8rem; margin: 1.5rem 0 1rem; color: #16213e; }}
        h2 {{ font-size: 1.4rem; margin: 2rem 0 0.8rem; color: #0f3460;
              border-bottom: 2px solid #e2e8f0; padding-bottom: 0.3rem; }}
        h3 {{ font-size: 1.1rem; margin: 1.2rem 0 0.5rem; color: #1a1a2e; }}
        p {{ margin-bottom: 1rem; }}
        li {{ margin-left: 1.5rem; margin-bottom: 0.4rem; }}
        a {{ color: #0f3460; }}
        strong {{ color: #16213e; }}
        hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 2rem 0; }}
        em {{ color: #64748b; font-size: 0.9rem; }}
        .updated {{ color: #64748b; font-size: 0.85rem; margin-top: 2rem; }}
    </style>
</head>
<body>
    {html_body}
    <p class="updated">Обновлено: {date}</p>
</body>
</html>"""

    with open(f"{config.DOCS_DIR}/index.html", "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    run_summary()
