"""
Обёртка для Gemini API (бесплатный уровень).
Автоматически перебирает модели, если основная недоступна.
"""
import json
import time
import requests
import config


# Модели в порядке приоритета (все бесплатные)
MODELS_TO_TRY = [
    "gemini-2.0-flash-lite",   # самый щедрый лимит (30 RPM)
    "gemini-2.0-flash",        # основная модель (15 RPM)
    "gemini-1.5-flash",        # старая, но стабильная (15 RPM)
]


def call_gemini(prompt: str, system_instruction: str = "", max_retries: int = 4) -> str:
    """
    Вызов Gemini API с автоматическим перебором моделей.
    Если одна модель даёт 429, пробуем следующую.
    """
    if not config.GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY не установлен! "
            "Получите бесплатный ключ: https://aistudio.google.com/apikey"
        )

    for model in MODELS_TO_TRY:
        print(f"  🔄 Пробуем модель: {model}")
        result = _try_model(model, prompt, system_instruction, max_retries)
        if result:
            return result
        print(f"  ⏭️ Модель {model} не сработала, пробуем следующую...")
        time.sleep(10)

    print("  [!] Все модели и попытки исчерпаны.")
    return ""


def _try_model(model: str, prompt: str, system_instruction: str, max_retries: int) -> str:
    """Попытка вызова конкретной модели."""
    url = f"{config.GEMINI_API_URL}/{model}:generateContent"
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
            resp = requests.post(url, params=params, json=body, timeout=120)

            if resp.status_code == 429:
                # Логируем детали ошибки
                try:
                    err_detail = resp.json().get("error", {}).get("message", "нет деталей")
                except:
                    err_detail = resp.text[:200]
                
                wait = 60 * (attempt + 1)  # 60, 120, 180, 240 сек
                print(f"  ⏳ Rate limit ({err_detail[:100]}), ждём {wait} сек (попытка {attempt + 1}/{max_retries})...")
                time.sleep(wait)
                continue

            if resp.status_code == 403:
                print(f"  ❌ Доступ запрещён для {model}. Пропускаем.")
                try:
                    err_msg = resp.json().get("error", {}).get("message", resp.text[:200])
                except:
                    err_msg = resp.text[:200]
                print(f"     Причина: {err_msg[:200]}")
                return ""  # Эту модель не пробуем повторно

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
                    print(f"  ✅ {model} ответил ({len(text)} символов)")
                    return text

            # Проверяем блокировку контента
            block_reason = data.get("promptFeedback", {}).get("blockReason", "")
            if block_reason:
                print(f"  [!] Запрос заблокирован: {block_reason}")
                return ""

            print(f"  [!] Пустой ответ (попытка {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(15)

        except requests.exceptions.Timeout:
            print(f"  [!] Таймаут (попытка {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(15)

        except requests.exceptions.RequestException as e:
            print(f"  [!] Ошибка (попытка {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(15)

    return ""
