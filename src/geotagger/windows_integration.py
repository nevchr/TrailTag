"""Stable Windows taskbar identity shared with the installed shortcut."""

import sys


APP_USER_MODEL_ID = "TrailTag.Desktop"


def configure_windows_identity() -> None:
    if sys.platform == "win32":
        import ctypes

        set_app_id = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        set_app_id.argtypes = [ctypes.c_wchar_p]
        set_app_id.restype = ctypes.c_long
        set_app_id(APP_USER_MODEL_ID)
