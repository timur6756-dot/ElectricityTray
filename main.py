import ctypes
import sys

from tray import TrayIcon

MUTEX_NAME = "ElectricityTray_SingleInstance_Mutex"


def acquire_single_instance():
    """
    Создаёт именованный Windows Mutex.

    Если Mutex уже существует,
    значит ElectricityTray уже запущен.
    """

    kernel32 = ctypes.windll.kernel32

    mutex = kernel32.CreateMutexW(
        None,
        False,
        MUTEX_NAME,
    )

    if not mutex:
        return None

    ERROR_ALREADY_EXISTS = 183

    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(mutex)

        return None

    return mutex


if __name__ == "__main__":

    mutex = acquire_single_instance()

    if mutex is None:
        # Вторая копия приложения
        # просто завершается.
        sys.exit(0)

    tray = TrayIcon()
    tray.run()
