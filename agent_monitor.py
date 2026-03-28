"""
Агент 1: Монитор.
Обходит все источники (RSS, YouTube, скрапинг) и собирает свежие материалы.
Чистый Python, без LLM.
"""
import json
import time
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

import config


def load_sources() -> dict:
    with open(config.SOURCES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_rss(url: str, source_name: str, topics: list[str]) -> list[dict]:
    """Получить записи из RSS-фида."""
    items = []
    try:
        feed = feedparser.parse(url)
        cutoff = datetime.now(timezone.utc) - timedelta(days=config.MAX_AGE_DAYS)

        for entry in feed.entries[: config.MAX_ITEMS_PER_SOURCE]:
            # Дата публикации
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

            if published and published < cutoff:
                continue

            summary = ""
            if hasattr(entry, "summary"):
                soup = BeautifulSoup(entry.summary, "html.parser")
                summary = soup.get_text()[:500]

            item_id = hashlib.md5(entry.get("link", entry.get("title", "")).encode()).hexdigest()

            items.append({
                "id": item_id,
                "source": source_name,
                "title": entry.get("title", "Без заголовка"),
                "url": entry.get("link", ""),
                "date": published.isoformat() if published else "",
                "summary": summary,
                "topics": topics,
            })
    except Exception as e:
        print(f"  [!] Ошибка RSS {source_name}: {e}")
    return items


def scrape_page(url: str, source_name: str, topics: list[str]) -> list[dict]:
    """Скрапинг страницы — находит ссылки на статьи/публикации."""
    items = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ExpertMonitorBot/1.0; +https://github.com)"
        }
        resp = requests.get(url, headers=headers, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Ищем ссылки, которые выглядят как статьи
        seen = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            title = a_tag.get_text(strip=True)

            # Фильтруем: нужны содержательные ссылки
            if not title or len(title) < 15 or len(title) > 300:
                continue
            if href.startswith("#") or href.startswith("mailto:"):
                continue
            if any(skip in href for skip in ["/tag/", "/category/", "/author/", "login", "signup"]):
                continue

            # Абсолютный URL
            if href.startswith("/"):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            elif not href.startswith("http"):
                continue

            if href in seen:
                continue
            seen.add(href)

            item_id = hashlib.md5(href.encode()).hexdigest()
            items.append({
                "id": item_id,
                "source": source_name,
                "title": title,
                "url": href,
                "date": "",
                "summary": "",
                "topics": topics,
            })

            if len(items) >= config.MAX_ITEMS_PER_SOURCE:
                break

    except Exception as e:
        print(f"  [!] Ошибка скрапинга {source_name}: {e}")
    return items


def run_monitor() -> list[dict]:
    """Основной цикл мониторинга."""
    sources = load_sources()
    all_items = []
    total_sources = 0

    print("=" * 60)
    print("АГЕНТ 1: МОНИТОР")
    print("=" * 60)

    # 1. Эксперты
    print("\n📚 Эксперты:")
    for expert in sources.get("experts", []):
        for src in expert.get("sources", []):
            name = f"{expert['name']} — {src['name']}"
            topics = expert.get("topics", [])
            rss_url = src.get("rss")

            if rss_url:
                print(f"  RSS: {name}")
                items = fetch_rss(rss_url, name, topics)
                all_items.extend(items)
                print(f"    → {len(items)} записей")
                total_sources += 1
                time.sleep(config.REQUEST_DELAY)

    # 2. Think tanks
    print("\n🏛️ Think tanks:")
    for tt in sources.get("think_tanks", []):
        name = tt["name"]
        topics = tt.get("topics", [])

        if tt.get("rss"):
            print(f"  RSS: {name}")
            items = fetch_rss(tt["rss"], name, topics)
            all_items.extend(items)
            print(f"    → {len(items)} записей")
        elif tt.get("scrape_url"):
            print(f"  Скрапинг: {name}")
            items = scrape_page(tt["scrape_url"], name, topics)
            all_items.extend(items)
            print(f"    → {len(items)} записей")

        total_sources += 1
        time.sleep(config.REQUEST_DELAY)

    # 3. Чешские и украинские источники
    print("\n🇨🇿🇺🇦 Чехия / Украина / ЕС:")
    for src in sources.get("czech_ukraine_sources", []):
        name = src["name"]
        topics = src.get("topics", [])

        if src.get("rss"):
            print(f"  RSS: {name}")
            items = fetch_rss(src["rss"], name, topics)
            all_items.extend(items)
            print(f"    → {len(items)} записей")
        elif src.get("scrape_url"):
            print(f"  Скрапинг: {name}")
            items = scrape_page(src["scrape_url"], name, topics)
            all_items.extend(items)
            print(f"    → {len(items)} записей")

        total_sources += 1
        time.sleep(config.REQUEST_DELAY)

    # 4. Data sources (RSS only)
    print("\n📊 Данные:")
    for ds in sources.get("data_sources", []):
        if ds.get("rss"):
            name = ds["name"]
            print(f"  RSS: {name}")
            items = fetch_rss(ds["rss"], name, ds.get("topics", []))
            all_items.extend(items)
            print(f"    → {len(items)} записей")
            total_sources += 1
            time.sleep(config.REQUEST_DELAY)

    # Дедупликация по ID
    seen_ids = set()
    unique_items = []
    for item in all_items:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            unique_items.append(item)

    print(f"\n✅ Итого: {len(unique_items)} уникальных записей из {total_sources} источников")

    # Сохраняем
    Path("data").mkdir(exist_ok=True)
    with open(config.RAW_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(unique_items, f, ensure_ascii=False, indent=2)

    print(f"💾 Сохранено в {config.RAW_ITEMS_FILE}")
    return unique_items


if __name__ == "__main__":
    run_monitor()
