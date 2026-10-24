import os
import sys
import threading
import traceback
import faulthandler
from datetime import datetime

from kivy.utils import platform

PRIVATE_DIR = "/storage/emulated/0/Folyan"
CRASH_FILE = os.path.join(PRIVATE_DIR, "crash.log")
MAX_LOG_BYTES = 16 * 1024 * 1024
KEEP_LOG_BYTES = 8 * 1024 * 1024

os.makedirs(PRIVATE_DIR, exist_ok=True)
_native_log = open(CRASH_FILE, "a", encoding="utf-8")
faulthandler.enable(file=_native_log, all_threads=True)


def _trim_log(extra_bytes):
    size = os.path.getsize(CRASH_FILE)
    if size + extra_bytes <= MAX_LOG_BYTES:
        return
    with open(CRASH_FILE, "rb") as f:
        f.seek(max(0, size - KEEP_LOG_BYTES))
        tail = f.read()
    cut = tail.find(b"\n")
    if cut != -1:
        tail = tail[cut + 1:]
    with open(CRASH_FILE, "wb") as f:
        f.write("... старые записи обрезаны ...\n".encode("utf-8") + tail)


def log_crash(exc_type, exc_value, exc_tb):
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = f"\n===== {stamp} =====\n{text}"
    _trim_log(len(record.encode("utf-8")))
    with open(CRASH_FILE, "a", encoding="utf-8") as f:
        f.write(record)


def _thread_excepthook(args):
    log_crash(args.exc_type, args.exc_value, args.exc_traceback)


sys.excepthook = log_crash
threading.excepthook = _thread_excepthook


def ask_storage_access():
    if platform != "android":
        return
    from jnius import autoclass

    Build_VERSION = autoclass("android.os.Build$VERSION")
    Environment = autoclass("android.os.Environment")

    if Build_VERSION.SDK_INT >= 30:
        if not Environment.isExternalStorageManager():
            from android import mActivity

            Intent = autoclass("android.content.Intent")
            Settings = autoclass("android.provider.Settings")
            Uri = autoclass("android.net.Uri")

            intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
            intent.setData(Uri.parse("package:" + mActivity.getPackageName()))
            mActivity.startActivity(intent)
    else:
        from android.permissions import request_permissions, Permission

        request_permissions([
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
        ])


def main():
    _trim_log(0)
    with open(CRASH_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n----- start {datetime.now():%Y-%m-%d %H:%M:%S} pid={os.getpid()} -----\n")

    try:
        ask_storage_access()
        from core import FolyanApp
        FolyanApp().run()
    except BaseException:
        log_crash(*sys.exc_info())
        raise


if __name__ == "__main__":
    main()
