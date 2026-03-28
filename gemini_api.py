"""
Обёртка для Gemini API (бесплатный уровень).
"""
import json
import time
import requests
import config


def call_gemini(prompt: str, system_instruction: str = "", max_retries: int = 6) -> str:
    """
    Вызов Gemini Flash API.
    Бесплатный лимит: 15 запросов/мин, 1M токенов/день.
    Новые ключи могут иметь более строгие лимиты в первые часы.
    """
    if not config.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY не установлен! "
            "Получите бесплатный ключ: https://aistudio.google.com/apikey"
        )

    url = f"{config.GEMINI_API_URL}/{config.GEMINI_MODEL}:generateContent"
    params = {"key": config.GEMINI_API_KEY}

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": config.GEMINI_MAX_OUTPUT_TOKENS,
            "temperature": 0.3,
        },
    }

    if system_instruction:
        body["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    for attempt in range(max_retries):
        try:
            resp = requests.post(
                url, params=params, json=body, timeout=120
            )

            if resp.status_code == 429:
                # Увеличенные паузы: 30, 60, 90, 120, 150, 180 сек
                wait = 30 * (attempt + 1)
                print(f"  ⏳ Rate limit, ждём {wait} сек (попытка {attempt + 1}/{max_retries})...")
                time.sleep(wait)
                continue

            if resp.status_code == 503:
                wait = 30 * (attempt + 1)
                print(f"  ⏳ Сервис недоступен, ждём {wait} сек...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()

            # Извлекаем текст ответа
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)
                if text:
                    print(f"  ✅ Gemini ответил ({len(text)} символов)")
                    return text

            # Проверяем блокировку контента
            block_reason = data.get("promptFeedback", {}).get("blockReason", "")
            if block_reason:
                print(f"  [!] Запрос заблокирован Gemini: {block_reason}")
                return ""

            print(f"  [!] Пустой ответ от Gemini (попытка {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(15)
                continue

        except requests.exceptions.Timeout:
            print(f"  [!] Таймаут Gemini (попытка {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(15)
                continue

        except requests.exceptions.RequestException as e:
            print(f"  [!] Ошибка Gemini (попытка {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(15)
            else:
                raise

    print("  [!] Все попытки исчерпаны.")
    return ""
