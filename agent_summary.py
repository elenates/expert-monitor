"""
Агент 4: Саммари.
Генерирует финальный отчёт на русском языке в формате Markdown.
Фокус: конкретика, цифры, практические действия.
"""
import json
from datetime import datetime
from pathlib import Path

import config
from gemini_api import call_gemini


SYSTEM_PROMPT = """Ты пишешь ежемесячную аналитическую записку для КОНКРЕТНОГО человека:
- Женщина, живёт в Брно, Чехия
- Работает в IT или смежной области
- Владеет квартирой в Украине
- Следит за глобальными макротрендами, чтобы принимать личные финансовые решения
- Читала книги Далио, Турчина, Хоува — пересказывать теории НЕ НАДО

Ты — умный друг с финансовым образованием. За кофе рассказываешь,
что важного произошло и что конкретно делать.

ЖЕЛЕЗНЫЕ ПРАВИЛА:

1. ЗАПРЕЩЁННЫЕ ФРАЗЫ (использование = провал):
   "стоит мониторить", "стоит отслеживать", "рассмотри возможность",
   "скорректируй расходы", "диверсифицируй", "будь осторожна",
   "обрати внимание", "оцени риски", "продолжай следить", 
   "не принимай панических решений", "оцени необходимость".
   Это пустые советы. ВМЕСТО НИХ — конкретные действия.

2. ЗАПРЕЩЕНО писать "если нет конкретных изменений — продолжай следить".
   Если нет новых данных — НЕ ПИШИ этот раздел вообще. Напиши одну строку
   "Существенных изменений за месяц не было." и всё.

3. Каждый факт ДОЛЖЕН содержать цифру, дату или имя.

4. ИНВЕСТИЦИОННЫЕ СОВЕТЫ должны быть КОНКРЕТНЫМИ:
   ПЛОХО: "рассмотри консервативные инструменты"
   ХОРОШО: "На горизонте 3-5 лет перед кризисом 2030-х:
   - Облигации: чешские государственные (ČOAZ) дают ~4.5%, покупаются через любой чешский банк
   - Золото: можно через ETF (например iShares Gold через Degiro или XTB), сейчас ~$2100/oz
   - Акции: оборонка (Rheinmetall, BAE Systems) растёт из-за перевооружения ЕС;
     здравоохранение (Novo Nordisk, Roche) устойчиво к рецессии
   - НЕ покупать: высокорисковые tech-стартапы, криптовалюту с плечом, недвижимость в кредит"

5. БЛИЖНИЙ ВОСТОК — упоминай ТОЛЬКО если есть конкретное влияние на цены энергии
   в Чехии/ЕС. Не нужно описывать каждый конфликт. Одного абзаца достаточно.
   Если влияния нет — не упоминай вообще.

6. ПРИОРИТЕТ РЕГИОНОВ в отчёте:
   1) Чехия и личные финансы (50% отчёта)
   2) ЕС и еврозона (20%)
   3) Украина — только конкретные изменения для владельца квартиры (15%)
   4) Глобальные тренды, включая Ближний Восток (15%)

7. Рекомендации формулируй как ПРЯМЫЕ УКАЗАНИЯ:
   ПЛОХО: "оцени, нужна ли тебе эта покупка"
   ХОРОШО: "крупные покупки (машина, техника) лучше сделать сейчас, пока ставки 
   не выросли — или отложить на 2027, когда по прогнозу ITR будет дно цикла"

Формат: чистый Markdown, русский язык."""


def run_summary() -> str:
    """Генерирует финальный отчёт."""
    print("\n" + "=" * 60)
    print("АГЕНТ 4: САММАРИ")
    print("=" * 60)

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

    # Собираем тексты статей для анализа
    articles_text = ""
    sources_list = ""
    for i, item in enumerate(filtered_items[:20]):
        full_text = item.get("full_text", item.get("summary", ""))
        if full_text and not full_text.startswith("[Не удалось"):
            articles_text += (
                f"\n{'='*40}\n"
                f"СТАТЬЯ: {item['title']}\n"
                f"ИСТОЧНИК: {item['source']}\n"
                f"ДАТА: {item.get('date', '?')}\n"
                f"ТЕКСТ: {full_text[:2500]}\n"
            )
        sources_list += f"- [{item['title']}]({item['url']}) — {item['source']}\n"

    today = datetime.now().strftime("%Y-%m-%d")
    month_year_ru = datetime.now().strftime("%m.%Y")

    prompt = f"""## Полные тексты статей за этот месяц:
{articles_text[:25000]}

## Аналитика по Чехии/Украине/ЕС:
{json.dumps(context_data, ensure_ascii=False, indent=2)[:6000]}

## НАПИШИ ОТЧЁТ. Структура:

# Саммари — {month_year_ru}

## Главное за месяц

3-5 самых важных фактов из статей. Каждый = 2-3 предложения С ЦИФРАМИ.
Приоритет: Чехия/ЕС → глобальная экономика → геополитика.

## Чехия и твои финансы

Это ГЛАВНЫЙ раздел. Конкретные данные за этот месяц:
- Ставка ČNB (текущая, изменилась ли?)
- Инфляция в ЧР (число)
- Курс CZK/EUR 
- Цены на энергию (изменения)
- Рынок труда в IT (есть ли данные о сокращениях или росте?)
- Ипотека (средняя ставка, тренд)
- Что конкретно делать с деньгами ПРЯМО СЕЙЧАС:
  какие депозиты, какие инструменты, что покупать, что не покупать.
  Называй конкретные банки (Fio, ČSOB, Komerční), платформы (XTB, Degiro),
  инструменты (ČOAZ облигации, ETF тикеры).

Если данных по какому-то пункту нет в статьях — пропусти пункт. Не выдумывай.

## Европа и еврозона

Решения ЕЦБ, ставки, инфляция в еврозоне — только с цифрами.
Как это влияет на Чехию и на тебя лично.

## Украина: что нового для владельца квартиры

ТОЛЬКО конкретные изменения, которые влияют на владельца недвижимости:
- Новые законы о собственности иностранцев
- Курс гривны (число)
- Программы компенсаций за разрушенное жильё
- Изменения в налогообложении недвижимости
- Конкретные данные по ценам на жильё

Если НИЧЕГО из этого не изменилось — напиши ОДНУ строку:
"Существенных изменений для владельцев недвижимости за этот месяц не было."
НЕ ПИШИ "продолжай следить за ситуацией" — это бессмысленно.

## Что делать (3-5 пунктов)

Формат СТРОГО:
**[Конкретный факт]** → [Конкретное действие, которое можно сделать на этой неделе]

Включи хотя бы один пункт про инвестиции с КОНКРЕТНЫМИ инструментами:
- Назови конкретные ETF, облигации, секторы (тикеры, названия)
- Скажи, что НЕ покупать и почему
- Укажи конкретные банки/платформы, доступные из Чехии

## Источники

{sources_list}

---
*Саммари {month_year_ru}. Сгенерирован автоматически.*"""

    print("  📤 Генерируем финальный отчёт...")
    report = call_gemini(prompt, system_instruction=SYSTEM_PROMPT)

    if not report:
        print("  [!] Пустой отчёт от Gemini.")
        return ""

    # Сохраняем
    Path(config.REPORT_ARCHIVE_DIR).mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(exist_ok=True)

    with open(config.REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    archive_name = f"report_{today}.md"
    archive_path = Path(config.REPORT_ARCHIVE_DIR) / archive_name
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(report)

    generate_html_page(report, today)

    print(f"  ✅ Отчёт сохранён: {config.REPORT_FILE}")
    print(f"  📁 Архив: {archive_path}")
    print(f"  🌐 Веб-страница: {config.DOCS_DIR}/index.html")
    return report


def generate_html_page(markdown_content: str, date: str):
    """Генерирует HTML-страницу для GitHub Pages."""
    Path(config.DOCS_DIR).mkdir(exist_ok=True)

    import re

    html_body = markdown_content

    # Заголовки
    html_body = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)

    # Ссылки (ДО жирного/курсива)
    html_body = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html_body)

    # Жирный и курсив
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
    html_body = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', html_body)

    # Списки
    html_body = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^- (.+)$', r'<li>\1</li>', html_body, flags=re.MULTILINE)

    # Параграфы
    html_body = re.sub(r'\n\n', '</p>\n<p>', html_body)
    html_body = f'<p>{html_body}</p>'
    html_body = html_body.replace('<p>---</p>', '<hr>')
    html_body = html_body.replace('<p></p>', '')

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Саммари экспертных прогнозов — {date}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.8;
            color: #1a1a2e;
            background: #f8f9fa;
            max-width: 780px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}
        h1 {{ font-size: 1.7rem; margin: 1.5rem 0 1rem; color: #16213e; }}
        h2 {{ font-size: 1.3rem; margin: 2.5rem 0 0.8rem; color: #0f3460;
              border-bottom: 2px solid #e2e8f0; padding-bottom: 0.4rem; }}
        h3 {{ font-size: 1.1rem; margin: 1.2rem 0 0.5rem; color: #1a1a2e; }}
        p {{ margin-bottom: 1rem; }}
        li {{ margin-left: 1.5rem; margin-bottom: 0.5rem; line-height: 1.6; }}
        a {{ color: #0f3460; text-decoration: underline; }}
        a:hover {{ color: #e63946; }}
        strong {{ color: #16213e; }}
        hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 2rem 0; }}
        em {{ color: #64748b; font-size: 0.9rem; }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>"""

    with open(f"{config.DOCS_DIR}/index.html", "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    run_summary()
