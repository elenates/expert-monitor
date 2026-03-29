"""
Тест API-ключа Gemini.
Запусти локально или добавь временно в workflow, чтобы понять, в чём проблема.

Использование:
  export GEMINI_API_KEY="твой_ключ"
  python test_gemini.py
"""
import os
import json
import requests

API_KEY = os.environ.get("GEMINI_API_KEY", "")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

if not API_KEY:
    print("❌ GEMINI_API_KEY не задан!")
    print("   export GEMINI_API_KEY='твой_ключ'")
    exit(1)

print(f"🔑 Ключ: {API_KEY[:8]}...{API_KEY[-4:]}")
print()

# Шаг 1: Какие модели доступны?
print("=" * 50)
print("Шаг 1: Проверяем доступные модели...")
print("=" * 50)
try:
    resp = requests.get(
        f"{BASE_URL}/models",
        params={"key": API_KEY},
        timeout=15
    )
    print(f"  HTTP статус: {resp.status_code}")
    if resp.status_code == 200:
        models = resp.json().get("models", [])
        flash_models = [m["name"] for m in models if "flash" in m["name"].lower()]
        print(f"  Всего моделей: {len(models)}")
        print(f"  Flash-модели: {flash_models[:10]}")
    else:
        print(f"  Ответ: {resp.text[:500]}")
except Exception as e:
    print(f"  Ошибка: {e}")

# Шаг 2: Тестируем конкретные модели
MODELS_TO_TRY = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
]

for model in MODELS_TO_TRY:
    print()
    print("=" * 50)
    print(f"Шаг 2: Тестируем модель {model}...")
    print("=" * 50)
    try:
        resp = requests.post(
            f"{BASE_URL}/models/{model}:generateContent",
            params={"key": API_KEY},
            json={
                "contents": [{"parts": [{"text": "Say hello in one word"}]}],
                "generationConfig": {"maxOutputTokens": 10}
            },
            timeout=30
        )
        print(f"  HTTP статус: {resp.status_code}")
        data = resp.json()

        if resp.status_code == 200:
            candidates = data.get("candidates", [])
            if candidates:
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                print(f"  ✅ РАБОТАЕТ! Ответ: '{text}'")
            else:
                print(f"  ⚠️ Пустой ответ: {json.dumps(data, indent=2)[:300]}")
        elif resp.status_code == 429:
            print(f"  ❌ Rate limit!")
            print(f"  Детали: {json.dumps(data, indent=2)[:500]}")
        elif resp.status_code == 403:
            print(f"  ❌ Доступ запрещён!")
            print(f"  Детали: {json.dumps(data, indent=2)[:500]}")
        else:
            print(f"  ❌ Ошибка: {json.dumps(data, indent=2)[:500]}")

    except Exception as e:
        print(f"  Ошибка: {e}")

print()
print("=" * 50)
print("ИТОГ")
print("=" * 50)
print("Если все модели возвращают 429 — проблема в ключе или аккаунте.")
print("Попробуй:")
print("  1. Создать новый ключ на https://aistudio.google.com/apikey")
print("  2. Сначала сделать тестовый запрос в AI Studio (чат), чтобы активировать ключ")
print("  3. Подождать 24 часа — новые ключи иногда имеют задержку активации")
