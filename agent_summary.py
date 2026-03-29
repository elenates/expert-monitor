"""
Агент 4: Саммари.
Генерирует финальный отчёт на русском языке в формате Markdown.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

import config
from gemini_api import call_gemini


def build_system_prompt(today_str, prev_month, prev2_month):
    return (
        "Ты пишешь ежемесячную записку для женщины из Брно (Чехия), IT-специалиста, "
        "владеющей квартирой в Украине. Она читала Далио, Турчина, Хоува — НЕ пересказывай.\n\n"
        "КРИТИЧЕСКОЕ ПРАВИЛО О ДАННЫХ:\n"
        f"Сегодня {today_str}. Статистика ВСЕГДА публикуется с задержкой 1-2 месяца. "
        f"Последние доступные данные — за {prev_month} или {prev2_month}. "
        "ЭТО НОРМАЛЬНО. Используй их. "
        f'Пиши: "по последним данным (за {prev_month}), инфляция составила X%". '
        'НИКОГДА не пиши "данные за текущий месяц отсутствуют". '
        "Если в статьях вообще нет цифр по теме — ПРОПУСТИ пункт целиком.\n\n"
        "ЗАПРЕЩЕНО (каждое нарушение = провал):\n"
        '- "данные отсутствуют" / "не указаны" / "информация не найдена"\n'
        '- "стоит мониторить" / "продолжай следить" / "обрати внимание"\n'
        '- "рассмотри возможность" / "оцени необходимость"\n'
        '- "может повлиять" без объяснения КАК и ЧТО ДЕЛАТЬ\n'
        "- Перечислять пункты, по которым нет данных\n\n"
        "ОБЯЗАТЕЛЬНО:\n"
        "- Каждый факт = цифра + дата + источник\n"
        "- Каждый вывод = КОНКРЕТНОЕ действие (купи/продай/подожди/зафиксируй)\n"
        '- Вместо "может повлиять на банки" пиши "банковские акции вырастут/упадут, '
        'поэтому покупай/не покупай X"\n'
        "- Инвестиции: называй тикеры, банки, платформы из Чехии\n"
        "- Ближний Восток: макс 1 абзац, только если влияет на цены энергии\n"
        '- Нет данных = не пиши раздел. Одна строка "Новых данных нет."\n'
        "- Каждый новый пункт — с новой строки\n"
        "- Списки источников — каждый источник на отдельной строке\n\n"
        "Формат: Markdown, русский. Пиши как умный друг, не как аналитик."
    )


def run_summary():
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

    articles_text = ""
    sources_list = ""
    for i, item in enumerate(filtered_items[:20]):
        full_text = item.get("full_text", item.get("summary", ""))
        if full_text and not full_text.startswith("[Не удалось"):
            articles_text += "\n" + "=" * 40 + "\n"
            articles_text += "СТАТЬЯ: " + item["title"] + "\n"
            articles_text += "ИСТОЧНИК: " + item["source"] + "\n"
            articles_text += "ДАТА: " + item.get("date", "?") + "\n"
            articles_text += "ТЕКСТ: " + full_text[:2500] + "\n"

        sources_list += "- [" + item["title"] + "](" + item["url"] + ") — " + item["source"] + "\n"

    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    month_year_ru = today.strftime("%m.%Y")

    prev1 = today.replace(day=1) - timedelta(days=1)
    prev2 = prev1.replace(day=1) - timedelta(days=1)
    prev_month = prev1.strftime("%B %Y")
    prev2_month = prev2.strftime("%B %Y")

    system_prompt = build_system_prompt(today_str, prev_month, prev2_month)

    prompt = (
        "## Полные тексты статей:\n"
        + articles_text[:25000]
        + "\n\n## Аналитика по регионам:\n"
        + json.dumps(context_data, ensure_ascii=False, indent=2)[:6000]
        + "\n\n## НАПИШИ ОТЧЁТ:\n\n"
        + "# Саммари — " + month_year_ru + "\n\n"
        + "## Главное за месяц\n\n"
        + "3-5 фактов. Каждый = отдельный абзац с цифрами.\n\n"
        + "## Чехия и твои финансы\n\n"
        + "Пиши ТОЛЬКО пункты, по которым ЕСТЬ цифры в статьях.\n"
        + "Используй последние доступные данные (за " + prev_month + " или " + prev2_month + ").\n"
        + "Укажи период. НЕ извиняйся за отсутствие свежих данных.\n"
        + "Пункт без цифры = НЕ ПИШИ его вообще.\n\n"
        + "Отдельно: **Что делать с деньгами.**\n"
        + "Конкретные банки (Fio, ČSOB, Komerční), платформы (XTB, Degiro),\n"
        + "инструменты (ČOAZ, ETF тикеры). Что покупать, что НЕ покупать.\n\n"
        + "## Европа и еврозона\n\n"
        + "Решения ЕЦБ, ставки — последние доступные цифры.\n"
        + "Каждый факт → что это значит и что делать. Не пиши 'может повлиять'.\n\n"
        + "## Украина: что нового для владельца квартиры\n\n"
        + "Только конкретные изменения: законы, курс гривны, компенсации, цены.\n"
        + 'Если ничего — одна строка: "Новых данных нет."\n\n'
        + "## Что делать (3-5 пунктов)\n\n"
        + "Каждый пункт с новой строки:\n\n"
        + "**[Факт с цифрой]** → [Действие на этой неделе]\n\n"
        + "Минимум один пункт про инвестиции с тикерами и платформами.\n\n"
        + "## Источники\n\n"
        + sources_list + "\n"
        + "---\n"
        + "*Саммари " + month_year_ru + ".*"
    )

    print("  📤 Генерируем финальный отчёт...")
    report = call_gemini(prompt, system_instruction=system_prompt)

    if not report:
        print("  [!] Пустой отчёт от Gemini.")
        return ""

    Path(config.REPORT_ARCHIVE_DIR).mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(exist_ok=True)

    with open(config.REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    archive_name = "report_" + today_str + ".md"
    archive_path = Path(config.REPORT_ARCHIVE_DIR) / archive_name
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(report)

    generate_html_page(report, today_str)

    print("  ✅ Отчёт сохранён: " + config.REPORT_FILE)
    print("  📁 Архив: " + str(archive_path))
    print("  🌐 Веб-страница: " + config.DOCS_DIR + "/index.html")
    return report


def generate_html_page(markdown_content, date):
    Path(config.DOCS_DIR).mkdir(exist_ok=True)

    import re

    h = markdown_content

    h = re.sub(r'^# (.+)$', r'<h1>\1</h1>', h, flags=re.MULTILINE)
    h = re.sub(r'^## (.+)$', r'<h2>\1</h2>', h, flags=re.MULTILINE)
    h = re.sub(r'^### (.+)$', r'<h3>\1</h3>', h, flags=re.MULTILINE)
    h = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', h)
    h = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', h)
    h = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', h, flags=re.MULTILINE)
    h = re.sub(r'^- (.+)$', r'<li>\1</li>', h, flags=re.MULTILINE)
    h = re.sub(r'\n\n', '</p>\n<p>', h)
    h = '<p>' + h + '</p>'
    h = h.replace('<p>---</p>', '<hr>')
    h = h.replace('<p></p>', '')

    css = """* { margin: 0; padding: 0; box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.8; color: #1a1a2e; background: #f8f9fa;
    max-width: 780px; margin: 0 auto; padding: 2rem 1.5rem;
}
h1 { font-size: 1.7rem; margin: 1.5rem 0 1rem; color: #16213e; }
h2 { font-size: 1.3rem; margin: 2.5rem 0 0.8rem; color: #0f3460;
     border-bottom: 2px solid #e2e8f0; padding-bottom: 0.4rem; }
p { margin-bottom: 1rem; }
li { margin-left: 1.5rem; margin-bottom: 0.5rem; line-height: 1.6; }
a { color: #0f3460; text-decoration: underline; }
a:hover { color: #e63946; }
strong { color: #16213e; }
hr { border: none; border-top: 1px solid #e2e8f0; margin: 2rem 0; }
em { color: #64748b; font-size: 0.9rem; }"""

    page = (
        '<!DOCTYPE html>\n<html lang="ru">\n<head>\n'
        '    <meta charset="UTF-8">\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '    <title>Саммари — ' + date + '</title>\n'
        '    <style>' + css + '</style>\n'
        '</head>\n<body>\n'
        + h +
        '\n</body>\n</html>'
    )

    out_path = Path(config.DOCS_DIR) / "index.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)


if __name__ == "__main__":
    run_summary()
