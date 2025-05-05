# backend/__init__.py
import os
import sys

# не загружаем .env, если мы в pytest
if not any("pytest" in arg for arg in sys.argv):
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    except ImportError:
        pass
