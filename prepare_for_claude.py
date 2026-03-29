"""
Подготовка файла для ручного саммари в Claude.
Берёт отфильтрованные статьи и собирает в компактный markdown.
Обновляет docs/index.html со статусом и ссылкой.
"""
import json
from datetime import datetime
from pathlib import Path

import config


def run_prepare():
    print("\n" + "=" * 60)
    print("ПОДГОТОВКА ФАЙЛА ДЛЯ CLAUDE")
    print("=" * 60)

    filtered_items = []
    if Path(config.FILTERED_FILE).exists():
        with open(config.FILTERED_FILE, "r", encoding="utf-8") as f:
            filtered_items = json.load(f)

    if not filtered_items:
        print("  [!] Нет отфильтрованных материалов.")
        return

    knowledge_base = ""
    if Path(config.KNOWLEDGE_BASE_FILE).exists():
        kb = Path(config.KNOWLEDGE_BASE_FILE).read_text(encoding="utf-8")
        if "## ОБЩАЯ КАРТИНА" in kb:
            knowledge_base = kb[kb.index("## ОБЩАЯ КАРТИНА"):]
        else:
            knowledge_base = kb[-3000:]

    today = datetime.now().strftime("%Y-%m-%d")

    output = "# Данные для саммари — " + today + "\n\n"
    output += "## Краткая база знаний (ключевые тезисы экспертов)\n\n"
    output += knowledge_base + "\n\n"
    output += "---\n\n"
    output += "## Отфильтрованные материалы (" + str(len(filtered_items)) + " шт.)\n\n"

    sources_summary = []
    for i, item in enumerate(filtered_items[:25]):
        output += "### " + str(i + 1) + ". " + item["title"] + "\n\n"
        output += "- **Источник:** " + item["source"] + "\n"
        output += "- **URL:** " + item["url"] + "\n"
        if item.get("date"):
            output += "- **Дата:** " + item["date"] + "\n"
        if item.get("relevance_reason"):
            output += "- **Почему отобрано:** " + item["relevance_reason"] + "\n"
        output += "\n"

        full_text = item.get("full_text", "")
        if full_text and not full_text.startswith("[Не удалось"):
            output += full_text[:2000] + "\n\n"
        elif item.get("summary"):
            output += item["summary"][:500] + "\n\n"

        output += "---\n\n"
        sources_summary.append(item["source"] + ": " + item["title"][:60])

    # Сохраняем
    out_path = "data/for_claude.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    Path(config.DOCS_DIR).mkdir(exist_ok=True)
    docs_path = config.DOCS_DIR + "/for_claude.md"
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(output)

    # Обновляем index.html
    update_index_html(today, len(filtered_items), sources_summary[:10])

    size_kb = len(output.encode("utf-8")) / 1024
    print("  ✅ Файл готов: " + out_path + " (" + str(round(size_kb)) + " KB)")
    print("  📋 Копия: " + docs_path)
    print("  🌐 Страница обновлена: " + config.DOCS_DIR + "/index.html")


def update_index_html(date, count, top_sources):
    sources_html = ""
    for s in top_sources:
        sources_html += "        <li>" + s + "</li>\n"

    html = (
        '<!DOCTYPE html>\n<html lang="ru">\n<head>\n'
        '    <meta charset="UTF-8">\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '    <title>Expert Monitor</title>\n'
        '    <style>\n'
        '        * { margin: 0; padding: 0; box-sizing: border-box; }\n'
        '        body {\n'
        '            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;\n'
        '            line-height: 1.8; color: #1a1a2e; background: #f8f9fa;\n'
        '            max-width: 700px; margin: 0 auto; padding: 2rem 1.5rem;\n'
        '        }\n'
        '        h1 { font-size: 1.7rem; margin-bottom: 0.5rem; color: #16213e; }\n'
        '        h2 { font-size: 1.2rem; margin: 2rem 0 0.8rem; color: #0f3460; }\n'
        '        .status { background: #e8f5e9; border-radius: 8px; padding: 1.2rem; margin: 1.5rem 0; }\n'
        '        .status strong { color: #2e7d32; }\n'
        '        .btn {\n'
        '            display: inline-block; background: #0f3460; color: #fff;\n'
        '            padding: 0.7rem 1.5rem; border-radius: 6px; text-decoration: none;\n'
        '            margin: 1rem 0.5rem 1rem 0; font-size: 0.95rem;\n'
        '        }\n'
        '        .btn:hover { background: #1a4a8a; }\n'
        '        .steps { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.2rem 1.5rem; }\n'
        '        .steps li { margin-bottom: 0.6rem; }\n'
        '        li { margin-left: 1.2rem; margin-bottom: 0.3rem; font-size: 0.95rem; }\n'
        '        .muted { color: #64748b; font-size: 0.85rem; margin-top: 2rem; }\n'
        '    </style>\n'
        '</head>\n<body>\n'
        '    <h1>Expert Monitor</h1>\n'
        '    <p>Мониторинг экспертных прогнозов: Далио, Турчин, Хоув, ITR Economics и др.</p>\n\n'
        '    <div class="status">\n'
        '        <strong>Последний сбор данных:</strong> ' + date + '<br>\n'
        '        <strong>Отобрано материалов:</strong> ' + str(count) + '\n'
        '    </div>\n\n'
        '    <a class="btn" href="for_claude.md">Скачать файл для Claude</a>\n\n'
        '    <h2>Как получить саммари</h2>\n'
        '    <div class="steps">\n'
        '        <ol>\n'
        '            <li>Скачай файл по кнопке выше</li>\n'
        '            <li>Открой <a href="https://claude.ai" target="_blank">claude.ai</a> — новый чат</li>\n'
        '            <li>Прикрепи файл + вставь промпт из <a href="https://github.com/elenates/expert-monitor/blob/main/PROMPT_TEMPLATE.md" target="_blank">PROMPT_TEMPLATE.md</a></li>\n'
        '            <li>Задавай уточняющие вопросы</li>\n'
        '        </ol>\n'
        '    </div>\n\n'
        '    <h2>Что в выборке</h2>\n'
        '    <ul>\n'
        + sources_html +
        '    </ul>\n\n'
        '    <p class="muted">Данные обновляются 1-го числа каждого месяца автоматически.</p>\n'
        '</body>\n</html>'
    )

    with open(config.DOCS_DIR + "/index.html", "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    run_prepare()
