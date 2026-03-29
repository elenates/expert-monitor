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
- Женщина, живёт в Праге, Чехия
- Работает (возможно IT или смежная область)
- Владеет квартирой в Украине
- Следит за глобальными макротрендами, чтобы принимать личные финансовые решения
- Читала книги Далио, Турчина, Хоува — пересказывать НЕ НАДО

Ты НЕ аналитик Bloomberg. Ты — умный друг, который прочитал все эти статьи 
и рассказывает за кофе: "Слушай, вот что важного произошло и вот что я бы сделал на твоём месте."

ЖЕЛЕЗНЫЕ ПРАВИЛА:
1. ЗАПРЕЩЕНЫ фразы: "стоит мониторить", "стоит отслеживать", "рассмотрите возможность",
   "скорректируйте расходы", "диверсифицируйте", "будьте осторожны", "обратите внимание".
   Это пустые советы. Вместо них — КОНКРЕТНЫЕ действия с цифрами.
2. Каждый факт ДОЛЖЕН содержать цифру, дату, или имя. Нет цифры = не пиши.
3. Каждая рекомендация = конкретное действие, которое можно сделать на этой неделе.
4. Пиши по-человечески, не канцелярским языком. Короткие предложения.
5. Если данных нет — напиши "Ничего нового". Это честнее, чем общие фразы.

ПЛОХО: "Стоит рассмотреть диверсификацию сбережений в различные валюты"
ХОРОШО: "ЕЦБ снизил ставку до 2.5%. Депозиты в EUR дают всё меньше. 
Конкретно: открой накопительный счёт в CZK в Fio Banka под 4.2% — это сейчас лучше, чем EUR."

ПЛОХО: "Следите за ситуацией на Ближнем Востоке"  
ХОРОШО: "Хуситы снова атакуют суда в Красном море. Цена нефти Brent выросла до $87. 
Для Чехии это +3-5% к счетам за электричество к лету. Если тариф не фиксированный — 
сейчас хороший момент зафиксировать."

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

## Аналитика по Чехии/Украине/Ближнему Востоку:
{json.dumps(context_data, ensure_ascii=False, indent=2)[:6000]}

## Список источников для раздела "Источники":
{sources_list}

## НАПИШИ ОТЧЁТ. Структура:

# Дайджест — {month_year_ru}

## Главное за месяц (3-5 пунктов)

Самые важные факты из прочитанных статей. Каждый пункт = 2-3 предложения.
Обязательно с цифрами. Пример формата:

**ITR Economics: реальные доходы падают.** В мартовском отчёте ITR отмечает, 
что реальные персональные доходы в США снизились на X% — это третий месяц подряд. 
По модели ITR, это один из индикаторов приближения к точке перелома 2030 года.

## Чехия: конкретика

Что РЕАЛЬНО изменилось за этот месяц. Только факты с цифрами:
ставка ČNB, курс кроны, инфляция, цены на энергию, рынок жилья.
Если конкретных новых данных нет — напиши "В этом месяце значимых изменений не было."

## Украина: конкретика

Конкретные изменения: фронт, экономика, гривна, законы о недвижимости.
Что это значит для владельца квартиры.
Если данных нет — "Существенных изменений для владельцев недвижимости не было."

## Ближний Восток и нефть

Конкретные события и их влияние на цены энергии для Чехии/ЕС.
Если данных нет — "Существенных изменений не было."

## Что делать (максимум 5 пунктов)

Формат СТРОГО такой:
1. **[Факт из статьи]** → [Конкретное действие на этой неделе]

Пример: **Нефть Brent выросла до $87 из-за атак хуситов** → Если у тебя 
нефиксированный тариф на электричество, зайди на сайт своего поставщика 
и зафиксируй тариф на год. В Чехии это можно сделать у ČEZ, innogy, E.ON.

ЗАПРЕЩЕНО: "мониторь ситуацию", "рассмотри возможности", "будь в курсе".
Только действия, которые можно СДЕЛАТЬ.

## Источники

{sources_list}

---
*Дайджест {month_year_ru}. Сгенерирован на основе {len(filtered_items)} источников.*"""

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

    # Экранируем HTML-спецсимволы в тексте, но сохраним markdown
    # (не нужно, т.к. контент приходит из LLM без HTML)

    # Заголовки
    html_body = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)

    # Ссылки (ДО обработки жирного/курсива, чтобы не ломать URL)
    html_body = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', html_body)

    # Жирный и курсив
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
    html_body = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', html_body)

    # Нумерованные списки
    html_body = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', html_body, flags=re.MULTILINE)

    # Маркированные списки
    html_body = re.sub(r'^- (.+)$', r'<li>\1</li>', html_body, flags=re.MULTILINE)

    # Параграфы
    html_body = re.sub(r'\n\n', '</p>\n<p>', html_body)
    html_body = f'<p>{html_body}</p>'

    # Горизонтальные линии
    html_body = html_body.replace('<p>---</p>', '<hr>')

    # Убираем пустые параграфы
    html_body = html_body.replace('<p></p>', '')

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Дайджест экспертных прогнозов — {date}</title>
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
        li {{ margin-left: 1.5rem; margin-bottom: 0.5rem; }}
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
