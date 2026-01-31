import sys
import os

# app/ ディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from handlers.webhook import handler as _webhook_handler  # noqa: E402


def handler(event, context):
    return _webhook_handler(event, context)
