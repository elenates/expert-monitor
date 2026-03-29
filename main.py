"""
Expert Monitor — главный оркестратор.
Собирает данные (Агент 1), фильтрует (Агент 2), готовит файл для Claude.
Саммари делается вручную в Claude Pro.

Использование:
    python main.py          # полный запуск
    python main.py --agent 1  # только сбор данных
    python main.py --agent 2  # только фильтрация
"""
import sys
import time
import argparse
from datetime import datetime

from agent_monitor import run_monitor
from agent_filter import run_filter
from prepare_for_claude import run_prepare


def main():
    parser = argparse.ArgumentParser(description="Expert Monitor Pipeline")
    parser.add_argument("--agent", type=int, choices=[1, 2],
                        help="Запустить только конкретного агента (1 или 2)")
    args = parser.parse_args()

    start_time = datetime.now()
    print("\n" + "=" * 60)
    print("🚀 EXPERT MONITOR — запуск " + start_time.strftime("%Y-%m-%d %H:%M"))
    print("=" * 60)

    try:
        if args.agent is None or args.agent == 1:
            run_monitor()

        if args.agent is None or args.agent == 2:
            if args.agent is None:
                print("\n⏳ Пауза 60 сек перед Gemini API...")
                time.sleep(60)
            run_filter()

        if args.agent is None:
            run_prepare()

        elapsed = (datetime.now() - start_time).total_seconds()
        print("\n" + "=" * 60)
        print("✅ ЗАВЕРШЕНО за " + str(int(elapsed)) + " секунд")
        print("📎 Скачай data/for_claude.md и открой новый чат в Claude")
        print("=" * 60)

    except Exception as e:
        print("\n❌ ОШИБКА: " + str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
