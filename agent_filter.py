"""
Агент 2: Фильтр.
Использует Gemini Flash для отбора релевантных материалов.
Сверяет с базой знаний (ключевые тезисы из книг).
"""
import json
from pathlib import Path

import config
from gemini_api import call_gemini


SYSTEM_PROMPT = """Ты — аналитик, специализирующийся на макроэкономических циклах, 
геополитике и системных рисках. Твоя задача — из списка найденных материалов 
отобрать те, которые НАИБОЛЕЕ релевантны для понимания текущей фазы 
большого цикла и прогнозирования будущих изменений.

Критерии отбора (в порядке приоритета):
1. Материал содержит НОВЫЕ прогнозы или обновления от ключевых экспертов
2. Материал подтверждает или опровергает тезисы из базы знаний
3. Материал содержит данные о системных рисках, поликризисе, долговых циклах
4. Материал касается геополитических сдвигов (USA-China, Россия-Украина, ЕС)
5. Материал содержит практические рекомендации для обычных людей

НЕ отбирать:
- Общие новости без аналитической глубины
- Маркетинговые материалы think tanks
- Устаревшие перепечатки"""


def run_filter() -> list[dict]:
    """Фильтрует raw_items через Gemini."""
    print("\n" + "=" * 60)
    print("АГЕНТ 2: ФИЛЬТР")
    print("=" * 60)

    # Загружаем сырые данные
    raw_path = Path(config.RAW_ITEMS_FILE)
    if not raw_path.exists():
        print("  [!] Файл raw_items.json не найден. Запустите сначала Агент 1.")
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

    # Формируем промпт
    items_text = ""
    for i, item in enumerate(raw_items):
        items_text += (
            f"\n--- Материал #{i+1} ---\n"
            f"Источник: {item['source']}\n"
            f"Заголовок: {item['title']}\n"
            f"Дата: {item.get('date', 'неизвестна')}\n"
            f"URL: {item['url']}\n"
            f"Описание: {item.get('summary', 'нет')[:300]}\n"
            f"Темы: {', '.join(item.get('topics', []))}\n"
        )

    prompt = f"""## База знаний (ключевые тезисы экспертов)

{knowledge_base[:15000]}

## Найденные материалы ({len(raw_items)} шт.)

{items_text}

## Задание

Из списка выше отбери 15-25 НАИБОЛЕЕ релевантных материалов.
Для каждого укажи:
- номер материала (число из "Материал #N")
- оценку релевантности (1-10)
- краткое обоснование (1 предложение): почему этот материал важен

Ответь СТРОГО в формате JSON (без markdown-обёртки):
{{
  "selected": [
    {{"index": 1, "score": 9, "reason": "..."}},
    ...
  ]
}}"""

    print(f"  📤 Отправляем {len(raw_items)} материалов в Gemini для фильтрации...")
    response = call_gemini(prompt, system_instruction=SYSTEM_PROMPT)

    # Парсим ответ
    try:
        # Убираем возможные markdown-обёртки
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
            clean = clean.rsplit("```", 1)[0]
        result = json.loads(clean)
    except json.JSONDecodeError:
        print(f"  [!] Не удалось распарсить ответ Gemini. Сохраняем все материалы.")
        # Fallback: берём всё
        result = {"selected": [{"index": i + 1, "score": 5, "reason": "auto"} for i in range(len(raw_items))]}

    selected = result.get("selected", [])
    filtered_items = []

    for sel in selected:
        idx = sel.get("index", 0) - 1
        if 0 <= idx < len(raw_items):
            item = raw_items[idx].copy()
            item["relevance_score"] = sel.get("score", 5)
            item["relevance_reason"] = sel.get("reason", "")
            filtered_items.append(item)

    # Сортируем по релевантности
    filtered_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    print(f"  ✅ Отобрано {len(filtered_items)} материалов из {len(raw_items)}")

    # Сохраняем
    with open(config.FILTERED_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_items, f, ensure_ascii=False, indent=2)

    print(f"  💾 Сохранено в {config.FILTERED_FILE}")
    return filtered_items


if __name__ == "__main__":
    run_filter()
