import ctypes
import sys

from tray import TrayIcon

MUTEX_NAME = "ElectricityTray_SingleInstance_Mutex"
ERROR_ALREADY_EXISTS = 183


def acquire_single_instance():
    """
    Create a named Windows mutex.

    If the mutex already exists, another instance of ElectricityTray
    is already running and the function returns None.
    """

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = (
        ctypes.c_void_p,
        ctypes.c_bool,
        ctypes.c_wchar_p,
    )

    kernel32.CloseHandle.restype = ctypes.c_bool
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)

    mutex = kernel32.CreateMutexW(
        None,
        False,
        MUTEX_NAME,
    )

    if not mutex:
        return None

    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(mutex)
        return None

    return mutex


if __name__ == "__main__":
    mutex = acquire_single_instance()

    if mutex is None:
        sys.exit(0)

    tray = TrayIcon()

    try:
        tray.run()
    finally:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CloseHandle.restype = ctypes.c_bool
        kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
        kernel32.CloseHandle(mutex)
