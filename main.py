import os
import sys
import threading
import traceback
from datetime import datetime

CRASH_DIR = "/storage/emulated/0/Folyan"
CRASH_FILE = os.path.join(CRASH_DIR, "crash.log")


def log_crash(exc_type, exc_value, exc_tb):
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = f"\n===== {stamp} =====\n{text}"
    try:
        os.makedirs(CRASH_DIR, exist_ok=True)
        with open(CRASH_FILE, "a", encoding="utf-8") as f:
            f.write(record)
    except Exception as e:
        print(f"Не удалось записать crash.log: {e}", file=sys.stderr)
    print(record, file=sys.stderr)


def _thread_excepthook(args):
    log_crash(args.exc_type, args.exc_value, args.exc_traceback)


sys.excepthook = log_crash
threading.excepthook = _thread_excepthook


def main():
    try:
        from core import FolyanApp
        FolyanApp().run()
    except BaseException:
        log_crash(*sys.exc_info())
        raise


if __name__ == "__main__":
    main()
