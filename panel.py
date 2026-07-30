import ctypes
import tkinter as tk
from datetime import datetime

import elering


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

        self.today_prices = elering.get_today_hourly_prices()
        self.today_stats = elering.get_day_stats(self.today_prices)

        self.tomorrow_prices = elering.get_tomorrow_hourly_prices()

        if len(self.tomorrow_prices) >= 20:
            self.tomorrow_stats = elering.get_day_stats(self.tomorrow_prices)
        else:
            self.tomorrow_stats = None

        self.root = tk.Tk()
        self.root.title("Electricity Estonia")

        self.window_width = 430
        self.window_height = 520

        self.root.geometry(f"{self.window_width}x{self.window_height}")

        self.root.resizable(False, False)

        self.build_interface()
        self.position_near_tray()

    def build_interface(self):
        """Создаёт интерфейс панели."""

        title = tk.Label(
            self.root,
            text="ELECTRICITY · ESTONIA",
            font=("Arial", 13, "bold"),
        )
        title.pack(pady=(12, 4))

        current = tk.Label(
            self.root,
            text=f"{self.current_price:.2f} c/kWh",
            font=("Arial", 28, "bold"),
        )
        current.pack()

        current_label = tk.Label(
            self.root,
            text="текущая биржевая цена",
            font=("Arial", 9),
        )
        current_label.pack()

        now = datetime.now()

        interval_minute = (now.minute // 15) * 15

        interval_text = f"{now.hour:02d}:" f"{interval_minute:02d}"

        interval_label = tk.Label(
            self.root,
            text=f"Текущий интервал: {interval_text}",
            font=("Arial", 9),
        )
        interval_label.pack(pady=(6, 2))

        if self.next_price is not None:
            next_text = f"Следующие 15 мин: " f"{self.next_price:.2f} c/kWh"
        else:
            next_text = "Следующая цена недоступна"

        next_label = tk.Label(
            self.root,
            text=next_text,
            font=("Arial", 10),
        )
        next_label.pack(pady=(0, 8))

        separator = tk.Frame(
            self.root,
            height=1,
            bg="gray",
        )
        separator.pack(
            fill="x",
            padx=15,
            pady=4,
        )

        today_title = tk.Label(
            self.root,
            text="Сегодня",
            font=("Arial", 11, "bold"),
        )
        today_title.pack(pady=(4, 2))

        if self.today_stats:
            stats_text = (
                f"Мин: "
                f"{self.today_stats['minimum']:.2f} "
                f"c/kWh в "
                f"{self.today_stats['minimum_time']}   |   "
                f"Макс: "
                f"{self.today_stats['maximum']:.2f} "
                f"c/kWh в "
                f"{self.today_stats['maximum_time']}\n"
                f"Средняя: "
                f"{self.today_stats['average']:.2f} "
                f"c/kWh"
            )

            stats_label = tk.Label(
                self.root,
                text=stats_text,
                font=("Arial", 9),
                justify="center",
            )
            stats_label.pack(pady=(0, 6))

        self.canvas = tk.Canvas(
            self.root,
            width=390,
            height=180,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )
        self.canvas.pack(pady=(2, 8))

        self.draw_today_chart()

        tomorrow_separator = tk.Frame(
            self.root,
            height=1,
            bg="gray",
        )
        tomorrow_separator.pack(
            fill="x",
            padx=15,
            pady=4,
        )

        tomorrow_title = tk.Label(
            self.root,
            text="Завтра",
            font=("Arial", 11, "bold"),
        )
        tomorrow_title.pack(pady=(4, 2))

        if self.tomorrow_stats:
            tomorrow_text = (
                f"Опубликовано: "
                f"{len(self.tomorrow_prices)} часов\n"
                f"Мин: "
                f"{self.tomorrow_stats['minimum']:.2f} "
                f"c/kWh   |   "
                f"Макс: "
                f"{self.tomorrow_stats['maximum']:.2f} "
                f"c/kWh\n"
                f"Средняя: "
                f"{self.tomorrow_stats['average']:.2f} "
                f"c/kWh"
            )
        else:
            tomorrow_text = "Полный профиль цен " "ещё не опубликован"

        tomorrow_label = tk.Label(
            self.root,
            text=tomorrow_text,
            font=("Arial", 9),
            justify="center",
        )
        tomorrow_label.pack(pady=(0, 8))

        close_button = tk.Button(
            self.root,
            text="Закрыть",
            command=self.root.destroy,
            width=12,
        )
        close_button.pack(pady=(4, 8))

    def draw_today_chart(self):
        """Рисует простой график почасовых цен."""

        if not self.today_prices:
            return

        values = [item["cents_kwh"] for item in self.today_prices]

        max_value = max(values)

        if max_value <= 0:
            max_value = 1

        chart_left = 30
        chart_top = 15
        chart_width = 340
        chart_height = 130

        self.canvas.create_line(
            chart_left,
            chart_top + chart_height,
            chart_left + chart_width,
            chart_top + chart_height,
        )

        self.canvas.create_line(
            chart_left,
            chart_top,
            chart_left,
            chart_top + chart_height,
        )

        count = len(values)

        if count < 2:
            return

        points = []

        for index, value in enumerate(values):
            x = chart_left + (index / (count - 1)) * chart_width

            y = chart_top + chart_height - (value / max_value) * chart_height

            points.extend(
                [
                    x,
                    y,
                ]
            )

        self.canvas.create_line(
            points,
            width=2,
            smooth=True,
        )

        for hour in [
            0,
            6,
            12,
            18,
            23,
        ]:
            x = chart_left + (hour / 23) * chart_width

            self.canvas.create_text(
                x,
                chart_top + chart_height + 15,
                text=f"{hour:02d}",
                font=("Arial", 8),
            )

        self.canvas.create_text(
            5,
            chart_top,
            text=f"{max_value:.1f}",
            anchor="w",
            font=("Arial", 8),
        )

        self.canvas.create_text(
            5,
            chart_top + chart_height,
            text="0",
            anchor="w",
            font=("Arial", 8),
        )

    def get_work_area(self):
        """Получает рабочую область Windows."""

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
        """Размещает панель над taskbar."""

        self.root.update_idletasks()

        try:
            work_area = self.get_work_area()

            margin_right = 10
            margin_bottom = 10

            x = work_area.right - self.window_width - margin_right

            y = work_area.bottom - self.window_height - margin_bottom

        except Exception:
            screen_width = self.root.winfo_screenwidth()

            screen_height = self.root.winfo_screenheight()

            x = screen_width - self.window_width - 10

            y = screen_height - self.window_height - 60

        self.root.geometry(f"{self.window_width}x" f"{self.window_height}" f"+{x}+{y}")

    def run(self):
        self.root.mainloop()
