"""
Агент 4: Саммари.
Генерирует финальный отчёт на русском языке в формате Markdown.
"""
import json
from datetime import datetime
from pathlib import Path

import config
from gemini_api import call_gemini


SYSTEM_PROMPT = """Ты — автор ежемесячного аналитического дайджеста для русскоязычного человека, 
живущего в Чехии и владеющего квартирой в Украине.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:

1. НЕ ПЕРЕСКАЗЫВАЙ общие теории из базы знаний. Читатель их уже знает.
2. ФОКУСИРУЙСЯ ТОЛЬКО на том, что НОВОГО произошло за этот месяц.
3. ПРИВОДИ КОНКРЕТНЫЕ цифры, даты, события, имена — из найденных материалов.
4. Если конкретных данных нет — честно напиши "за этот месяц конкретных новых данных нет".
5. КАЖДАЯ рекомендация должна быть привязана к конкретному текущему событию или тренду.
6. Пиши кратко. Лучше 3 конкретных факта, чем 3 абзаца общих слов.

ПЛОХОЙ пример (общие слова):
"Эксперты предсказывают нарастание нестабильности. Неравенство растёт."

ХОРОШИЙ пример (конкретика):
"ITR Economics опубликовал обновлённый прогноз: реальные доходы населения США 
снизились на 2.1% за последний квартал. Это подтверждает их тезис о приближении 
точки перелома к 2030 году."

Формат отчёта — чистый Markdown на русском языке."""


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

    # Полный текст материалов для анализа
    materials_detail = ""
    for i, item in enumerate(filtered_items[:25]):
        materials_detail += (
            f"\n### Материал #{i+1}\n"
            f"- Источник: {item['source']}\n"
            f"- Заголовок: {item['title']}\n"
            f"- URL: {item['url']}\n"
            f"- Дата: {item.get('date', 'неизвестна')}\n"
            f"- Описание: {item.get('summary', 'нет')[:500]}\n"
            f"- Почему релевантно: {item.get('relevance_reason', '')}\n"
        )

    today = datetime.now().strftime("%Y-%m-%d")
    month_year_ru = datetime.now().strftime("%m.%Y")

    prompt = f"""## Контекст Чехии и Украины (анализ):
{json.dumps(context_data, ensure_ascii=False, indent=2)[:8000]}

## Найденные материалы за этот период:
{materials_detail}

## Задание

Напиши аналитический дайджест. Структура ниже.
ПОМНИ: только конкретика из найденных материалов. Никаких общих слов.

---

# Дайджест — {month_year_ru}

## Что нового за месяц

Перечисли 5-7 КОНКРЕТНЫХ новых публикаций/данных/событий из найденных материалов.
Для каждого: что именно опубликовано, кем, какой вывод, и почему это важно.
Формат: короткий абзац на каждый пункт. Приводи цифры, если они есть в материалах.

## Сигналы по «большому циклу»

НЕ пересказывай теорию Далио/Турчина/Хоува. Вместо этого:
- Какие КОНКРЕТНЫЕ события этого месяца подтверждают или опровергают их прогнозы?
- Есть ли новые данные (долг, инфляция, неравенство, конфликты)?
- Появились ли неожиданные «чёрные лебеди»?
Если таких данных нет в материалах — напиши "в этом месяце значимых сигналов не обнаружено".

## Чехия: что изменилось

Только НОВЫЕ данные: решения ČNB, изменения ставок, новые данные по инфляции/занятости,
новые законы или регуляции. Если ничего конкретного — напиши прямо.

## Украина: обновление

- Ход войны: конкретные изменения на фронте или в переговорах (из ISW и других)
- Экономика: новые данные по гривне, ВВП, восстановлению
- Недвижимость: есть ли новые данные о ценах или законодательстве?
Если нет конкретных данных — напиши прямо.

## Ближний Восток: обновление

Конкретные изменения: эскалация/деэскалация конфликтов, влияние на цены нефти и энергии,
последствия для ЕС и Чехии. Если нет данных — напиши прямо.

## Что делать: конкретные шаги

Максимум 5 рекомендаций. КАЖДАЯ должна быть привязана к конкретному событию 
или тренду из этого месяца. Формат:
"[Событие/данные] → поэтому стоит [конкретное действие]"

ПЛОХО: "Диверсифицируйте сбережения"
ХОРОШО: "ČNB снизил ставку до X% → фиксированные депозиты в CZK теряют привлекательность, 
рассмотрите перевод части сбережений в EUR-фонды"

## Источники

Список использованных материалов с ссылками.

---
*Отчёт за {month_year_ru}. Следующий: {datetime.now().strftime('%d')}.{(datetime.now().month % 12) + 1:02d}.{datetime.now().year}*
"""

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
