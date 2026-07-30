import ctypes
import tkinter as tk
from datetime import datetime


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class PricePanel:

    def __init__(self, current_price, next_price):
        self.current_price = current_price
        self.next_price = next_price

        self.root = tk.Tk()
        self.root.title("Electricity Estonia")

        self.window_width = 320
        self.window_height = 220

        self.root.geometry(f"{self.window_width}x{self.window_height}")

        self.root.resizable(False, False)

        title = tk.Label(
            self.root,
            text="ELECTRICITY · ESTONIA",
            font=("Arial", 12, "bold"),
        )
        title.pack(pady=(15, 5))

        current = tk.Label(
            self.root,
            text=f"{self.current_price:.2f} c/kWh",
            font=("Arial", 28, "bold"),
        )
        current.pack(pady=(5, 0))

        current_label = tk.Label(
            self.root,
            text="сейчас",
            font=("Arial", 10),
        )
        current_label.pack()

        now = datetime.now()

        interval_minute = (now.minute // 15) * 15

        interval_text = f"{now.hour:02d}:" f"{interval_minute:02d}"

        time_label = tk.Label(
            self.root,
            text=f"Текущий интервал: {interval_text}",
            font=("Arial", 10),
        )
        time_label.pack(pady=(12, 5))

        if self.next_price is not None:
            next_text = f"Следующие 15 мин: " f"{self.next_price:.2f} c/kWh"
        else:
            next_text = "Следующая цена недоступна"

        next_label = tk.Label(
            self.root,
            text=next_text,
            font=("Arial", 11),
        )
        next_label.pack(pady=5)

        close_button = tk.Button(
            self.root,
            text="Закрыть",
            command=self.root.destroy,
            width=12,
        )
        close_button.pack(pady=15)

        self.position_near_tray()

    def get_work_area(self):
        """Получает рабочую область основного монитора Windows."""

        SPI_GETWORKAREA = 0x0030

        rect = RECT()

        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_GETWORKAREA,
            0,
            ctypes.byref(rect),
            0,
        )

        if not result:
            raise ctypes.WinError()

        return rect

    def position_near_tray(self):
        """Размещает панель в рабочей области Windows."""

        self.root.update_idletasks()

        try:
            work_area = self.get_work_area()

            margin_right = 10
            margin_bottom = 10

            x = work_area.right - self.window_width - margin_right

            y = work_area.bottom - self.window_height - margin_bottom

        except Exception:
            # Резервный вариант
            screen_width = self.root.winfo_screenwidth()

            screen_height = self.root.winfo_screenheight()

            x = screen_width - self.window_width - 10

            y = screen_height - self.window_height - 60

        self.root.geometry(f"{self.window_width}x" f"{self.window_height}" f"+{x}+{y}")

    def run(self):
        self.root.mainloop()
