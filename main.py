import os
import sys
import threading
import traceback
import faulthandler
import os
import sys
import threading
import traceback
import faulthandler
from datetime import datetime

from kivy.utils import platform

PRIVATE_DIR = "/storage/emulated/0/Folyan/FolyanApp/"
CRASH_FILE = os.path.join(PRIVATE_DIR, "crash.log")

_native_log = None
os.makedirs(PRIVATE_DIR, exist_ok=True)
_native_log = open(CRASH_FILE, "a", encoding="utf-8")
faulthandler.enable(file=_native_log, all_threads=True)


def log_crash(exc_type, exc_value, exc_tb):
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = f"\n===== {stamp} =====\n{text}"
    os.makedirs(PRIVATE_DIR, exist_ok=True)
    with open(CRASH_FILE, "a", encoding="utf-8") as f:
        f.write(record)

def _thread_excepthook(args):
    log_crash(args.exc_type, args.exc_value, args.exc_traceback)


sys.excepthook = log_crash
threading.excepthook = _thread_excepthook


def ask_storage_access():
    if platform != "android":
        return
    try:
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
    except Exception:
        log_crash(*sys.exc_info())


def main():
    try:
        with open(CRASH_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n----- start {datetime.now():%Y-%m-%d %H:%M:%S} pid={os.getpid()} -----\n")
    except Exception:
        pass

    ask_storage_access()

    try:
        from core import FolyanApp
        FolyanApp().run()
    except BaseException:
        log_crash(*sys.exc_info())
        raise


if __name__ == "__main__":
    main()
