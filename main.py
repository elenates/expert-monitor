"""
Expert Monitor — главный оркестратор.
Запускает все 4 агента последовательно.

Использование:
    python main.py          # полный запуск всех агентов
    python main.py --agent 1  # только Агент 1 (мониторинг)
    python main.py --agent 2  # только Агент 2 (фильтрация)
    python main.py --agent 3  # только Агент 3 (контекст)
    python main.py --agent 4  # только Агент 4 (саммари)
"""
import sys
import argparse
from datetime import datetime

from agent_monitor import run_monitor
from agent_filter import run_filter
from agent_context import run_context
from agent_summary import run_summary


def main():
    parser = argparse.ArgumentParser(description="Expert Monitor Pipeline")
    parser.add_argument("--agent", type=int, choices=[1, 2, 3, 4],
                        help="Запустить только конкретного агента (1-4)")
    args = parser.parse_args()

    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"🚀 EXPERT MONITOR — запуск {start_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    try:
        if args.agent is None or args.agent == 1:
            run_monitor()

        if args.agent is None or args.agent == 2:
            run_filter()

        if args.agent is None or args.agent == 3:
            run_context()

        if args.agent is None or args.agent == 4:
            run_summary()

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n{'='*60}")
        print(f"✅ ЗАВЕРШЕНО за {elapsed:.0f} секунд")
        print(f"{'='*60}")

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
