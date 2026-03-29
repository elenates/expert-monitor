"""
Агент 2: Фильтр + обогащение.
1. Через Gemini отбирает релевантные материалы из списка
2. Загружает полный текст топ-статей (чтобы саммари было конкретным)
"""
import json
import time
import hashlib
from pathlib import Path

import requests
from bs4 import BeautifulSoup

import config
from gemini_api import call_gemini


SYSTEM_PROMPT = """Ты — аналитик, специализирующийся на макроэкономических циклах, 
геополитике и системных рисках. Отбери наиболее релевантные материалы.

Критерии (в порядке приоритета):
1. НОВЫЕ данные, цифры, прогнозы (не общие обзоры)
2. Конкретные экономические индикаторы (ставки, инфляция, ВВП, долг)
3. Геополитические события (война, конфликты, санкции, переговоры)
4. Практические рекомендации от экспертов
5. Всё, что касается Чехии, Украины, ЕС, Ближнего Востока

НЕ отбирать: общие обзоры без цифр, маркетинг, анонсы мероприятий."""


def fetch_article_text(url: str, max_chars: int = 3000) -> str:
    """Загружает и извлекает текст статьи по URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ExpertMonitorBot/1.0)"
        }
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Удаляем навигацию, скрипты, стили
        for tag in soup.find_all(["nav", "script", "style", "header", "footer", "aside"]):
            tag.decompose()

        # Ищем основной контент
        article = soup.find("article") or soup.find("main") or soup.find("div", class_="content")
        if article:
            text = article.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)

        # Чистим пробелы
        text = " ".join(text.split())
        return text[:max_chars]

    except Exception as e:
        return f"[Не удалось загрузить: {e}]"


def run_filter() -> list[dict]:
    """Фильтрует raw_items через Gemini, затем обогащает контентом."""
    print("\n" + "=" * 60)
    print("АГЕНТ 2: ФИЛЬТР + ОБОГАЩЕНИЕ")
    print("=" * 60)

    raw_path = Path(config.RAW_ITEMS_FILE)
    if not raw_path.exists():
        print("  [!] Файл raw_items.json не найден.")
        return []

    with open(raw_path, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    if not raw_items:
        print("  [!] Нет материалов для фильтрации.")
        return []

    # Загружаем базу знаний
    kb_path = Path(config.KNOWLEDGE_BASE_FILE)
    knowledge_base = ""
    if kb_path.exists():
        knowledge_base = kb_path.read_text(encoding="utf-8")

    # --- Шаг 1: Фильтрация через Gemini ---
    items_text = ""
    for i, item in enumerate(raw_items):
        items_text += (
            f"\n--- #{i+1} ---\n"
            f"Источник: {item['source']}\n"
            f"Заголовок: {item['title']}\n"
            f"URL: {item['url']}\n"
            f"Описание: {item.get('summary', 'нет')[:200]}\n"
        )

    prompt = f"""## Ключевые темы для отслеживания:
{knowledge_base[:5000]}

## Материалы ({len(raw_items)} шт.):
{items_text}

## Задание
Отбери 15-20 НАИБОЛЕЕ релевантных (с конкретными данными, цифрами, прогнозами).
Ответь СТРОГО в JSON (без markdown):
{{"selected": [{{"index": 1, "score": 9, "reason": "..."}}]}}"""

    print(f"  📤 Фильтруем {len(raw_items)} материалов...")
    response = call_gemini(prompt, system_instruction=SYSTEM_PROMPT)

    try:
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
            clean = clean.rsplit("```", 1)[0]
        result = json.loads(clean)
    except json.JSONDecodeError:
        print("  [!] Ошибка парсинга. Берём первые 20.")
        result = {"selected": [{"index": i+1, "score": 5, "reason": "auto"} for i in range(min(20, len(raw_items)))]}

    selected = result.get("selected", [])
    filtered_items = []
    for sel in selected:
        idx = sel.get("index", 0) - 1
        if 0 <= idx < len(raw_items):
            item = raw_items[idx].copy()
            item["relevance_score"] = sel.get("score", 5)
            item["relevance_reason"] = sel.get("reason", "")
            filtered_items.append(item)

    filtered_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    print(f"  ✅ Отобрано {len(filtered_items)} материалов")

    # --- Шаг 2: Загрузка полного текста топ-15 статей ---
    print(f"\n  📖 Загружаем текст топ-{min(15, len(filtered_items))} статей...")
    for i, item in enumerate(filtered_items[:15]):
        url = item.get("url", "")
        if not url or not url.startswith("http"):
            continue
        print(f"    [{i+1}] {item['title'][:60]}...")
        text = fetch_article_text(url)
        item["full_text"] = text
        time.sleep(0.5)  # вежливая пауза

    print(f"  ✅ Текст загружен")

    # Сохраняем
    with open(config.FILTERED_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_items, f, ensure_ascii=False, indent=2)

    print(f"  💾 Сохранено в {config.FILTERED_FILE}")
    return filtered_items


if __name__ == "__main__":
    run_filter()
