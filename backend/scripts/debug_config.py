#!/usr/bin/env python3
import sys
from pathlib import Path
from backend.config_parser import read_config

def main():
    # Проверяем сразу обе возможные локации конфига
    candidates = [
        "config/config.conf",
        "backend/config/config.conf"
    ]

    for cfg_path in candidates:
        print(f"\n>>> Reading config from: {cfg_path}")
        try:
            cfg = read_config(cfg_path)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            continue

        # Выводим секции и пары ключ=значение
        for section, opts in cfg.items():
            print(f"[{section}]")
            for key, val in opts.items():
                print(f"{key} = {val}")
        print(">>> OK\n")

if __name__ == "__main__":
    main()
