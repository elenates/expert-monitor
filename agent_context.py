"""
Агент 3: Контекст Чехии и Украины.
Анализирует отфильтрованные материалы с точки зрения человека,
живущего в Чехии и имеющего отношение к Украине.
"""
import json
from pathlib import Path

import config
from gemini_api import call_gemini


SYSTEM_PROMPT = """Ты — аналитик, помогающий русскоязычному человеку, который:
- Живёт и работает в Чехии (Брно) в IT
- Имеет недвижимость в Украине
- Хочет понимать, как глобальные макротренды влияют на его жизнь

Твоя задача — проанализировать экспертные материалы через призму:

ЧЕХИЯ:
- Курс кроны (CZK) к евро и доллару, политика ČNB
- Рынок недвижимости Чехии (цены, доступность, ипотека)
- Рынок труда (IT, безработица)
- Энергетика и зависимость от поставщиков
- Отношения ЧР с ЕС, миграция, политическая обстановка
- Инфляция, стоимость жизни

УКРАИНА:
- Ход и перспективы войны (когда и как может закончиться, по мнению экспертов)
- Состояние экономики
- Рынок недвижимости (будет ли обвал или рост после войны)
- Программы восстановления (reconstruction) — какие регионы приоритетны
- Риски для собственности (разрушения, национализация, юридические вопросы)
- Перспективы вступления в ЕС и что это значит для рынка

ЕС В ЦЕЛОМ:
- Политика ЕЦБ, ставки, евро
- Энергопереход и его стоимость
- Демография и миграция
- Торговые войны и отношения с Китаем/США

Будь конкретным и практичным. Избегай общих фраз."""


def run_context() -> dict:
    """Добавляет чешский и украинский контекст к отфильтрованным материалам."""
    print("\n" + "=" * 60)
    print("АГЕНТ 3: КОНТЕКСТ ЧЕХИЯ / УКРАИНА")
    print("=" * 60)

    filtered_path = Path(config.FILTERED_FILE)
    if not filtered_path.exists():
        print("  [!] Файл filtered.json не найден. Запустите сначала Агент 2.")
        return {}

    with open(filtered_path, "r", encoding="utf-8") as f:
        filtered_items = json.load(f)

    if not filtered_items:
        print("  [!] Нет отфильтрованных материалов.")
        return {}

    # Формируем текст материалов
    materials_text = ""
    for i, item in enumerate(filtered_items[:25]):  # ограничиваем топ-25
        materials_text += (
            f"\n--- #{i+1} (релевантность: {item.get('relevance_score', '?')}/10) ---\n"
            f"Источник: {item['source']}\n"
            f"Заголовок: {item['title']}\n"
            f"URL: {item['url']}\n"
            f"Описание: {item.get('summary', 'нет')[:400]}\n"
            f"Почему отобран: {item.get('relevance_reason', '')}\n"
        )

    # Загружаем базу знаний для контекста
    kb_path = Path(config.KNOWLEDGE_BASE_FILE)
    knowledge_excerpt = ""
    if kb_path.exists():
        full_kb = kb_path.read_text(encoding="utf-8")
        # Берём только секцию "ОБЩАЯ КАРТИНА"
        if "## ОБЩАЯ КАРТИНА" in full_kb:
            knowledge_excerpt = full_kb[full_kb.index("## ОБЩАЯ КАРТИНА"):]
        else:
            knowledge_excerpt = full_kb[-3000:]

    prompt = f"""## Контекст: что говорят эксперты (общая картина)

{knowledge_excerpt}

## Отфильтрованные материалы за этот период

{materials_text}

## Задание

Проанализируй все материалы выше и дай оценку по ТРЁМ блокам. 
Отвечай на русском языке. Будь конкретным — приводи цифры, 
временные рамки, названия конкретных рисков.

Ответь в формате JSON (без markdown-обёртки):
{{
  "czech_context": {{
    "economy": "Анализ влияния на экономику ЧР (3-5 предложений)",
    "real_estate": "Что будет с рынком недвижимости в ЧР",
    "labor_market": "Рынок труда, зарплаты",
    "risks": ["Список конкретных рисков для жителя ЧР"],
    "opportunities": ["Возможности, если есть"]
  }},
  "ukraine_context": {{
    "war_outlook": "Перспективы войны по мнению экспертов",
    "economy": "Экономика Украины",
    "real_estate": "Прогноз для рынка недвижимости Украины",
    "reconstruction": "Перспективы восстановления",
    "property_risks": ["Конкретные риски для владельца квартиры"],
    "property_opportunities": ["Возможности"]
  }},
  "eu_context": {{
    "macro_trends": "Ключевые тренды для ЕС",
    "ecb_policy": "Политика ЕЦБ и её последствия",
    "energy": "Энергетическая ситуация",
    "risks": ["Системные риски для ЕС"]
  }}
}}"""

    print(f"  📤 Анализируем {len(filtered_items[:25])} материалов в чешском/украинском контексте...")
    response = call_gemini(prompt, system_instruction=SYSTEM_PROMPT)

    # Парсим
    try:
        clean = response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1]
            clean = clean.rsplit("```", 1)[0]
        context_data = json.loads(clean)
    except json.JSONDecodeError:
        print("  [!] Не удалось распарсить ответ. Сохраняем как текст.")
        context_data = {"raw_analysis": response}

    # Сохраняем
    with open(config.CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(context_data, f, ensure_ascii=False, indent=2)

    print(f"  ✅ Контекст сохранён в {config.CONTEXT_FILE}")
    return context_data


if __name__ == "__main__":
    run_context()
