"""
Подготовка файла для ручного саммари в Claude.
Берёт отфильтрованные статьи и собирает в компактный markdown,
который можно прикрепить к чату с Claude.
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
        # Берём только "ОБЩАЯ КАРТИНА"
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
            # Обрезаем до 2000 символов на статью
            output += full_text[:2000] + "\n\n"
        elif item.get("summary"):
            output += item["summary"][:500] + "\n\n"

        output += "---\n\n"

    # Сохраняем
    out_path = "data/for_claude.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    # Также кладём копию в docs для удобного скачивания с GitHub
    Path(config.DOCS_DIR).mkdir(exist_ok=True)
    docs_path = config.DOCS_DIR + "/for_claude.md"
    with open(docs_path, "w", encoding="utf-8") as f:
        f.write(output)

    size_kb = len(output.encode("utf-8")) / 1024
    print("  ✅ Файл готов: " + out_path + " (" + str(round(size_kb)) + " KB)")
    print("  📋 Копия: " + docs_path)
    print("  📎 Скачай его и прикрепи к чату с Claude вместе с промптом")


if __name__ == "__main__":
    run_prepare()
