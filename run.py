#!/usr/bin/env python3
"""
Скрипт для быстрого запуска AI-Tutor из Python.
ИСПОЛЬЗУЙТЕ: py -3.13 run.py (или просто run.bat на Windows)
"""

import sys
import os
import subprocess
from pathlib import Path

# Проверяем что используется Python 3.13
if sys.version_info < (3, 13):
    print(f"⚠️ Обнаружена Python {sys.version}")
    print("❌ Требуется Python 3.13 или выше")
    print("\nПожалуйста, используйте:")
    print("  py -3.13 run.py  (Windows)")
    print("  python3.13 run.py (Linux/Mac)")
    sys.exit(1)

# Добавляем корневую папку в sys.path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 AI-Tutor: Запуск приложения")
    print("=" * 60 + "\n")
    
    # Проверяем конфигурацию
    try:
        from config import validate_config
        if not validate_config():
            print("\n⚠️ Проверьте предупреждения конфигурации выше!")
            input("Нажмите Enter для продолжения...")
    except Exception as e:
        print(f"⚠️ Не удалось загрузить конфигурацию: {e}")
    
    # Запускаем главный модуль
    try:
        from main import main
        main()
    except KeyboardInterrupt:
        print("\n\n👋 AI-Tutor завершен пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
