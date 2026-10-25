from kivy.utils import platform


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
        pass


def main():
    ask_storage_access()
    from core import FolyanApp
    FolyanApp().run()


if __name__ == "__main__":
    main()
