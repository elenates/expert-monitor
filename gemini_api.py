"""
Обёртка для Gemini API (бесплатный уровень).
"""
import json
import time
import requests
import config


def call_gemini(prompt: str, system_instruction: str = "", max_retries: int = 3) -> str:
    """
    Вызов Gemini Flash API.
    Бесплатный лимит: 15 запросов/мин, 1M токенов/день.
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
            "temperature": 0.3,  # более детерминированный вывод
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
                wait = 15 * (attempt + 1)
                print(f"  ⏳ Rate limit, ждём {wait} сек...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()

            # Извлекаем текст ответа
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts)
            else:
                print(f"  [!] Пустой ответ от Gemini: {data}")
                return ""

        except requests.exceptions.RequestException as e:
            print(f"  [!] Ошибка Gemini (попытка {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))
            else:
                raise

    return ""
