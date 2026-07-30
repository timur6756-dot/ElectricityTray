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

    TOMORROW_REFRESH_MS = 15 * 60 * 1000

    def __init__(self, current_price, next_price):
        self.current_price = current_price
        self.next_price = next_price

        self.today_prices = []
        self.today_stats = None

        self.tomorrow_prices = []
        self.tomorrow_stats = None

        self.root = tk.Tk()
        self.root.title("Electricity Estonia")

        self.window_width = 430
        self.window_height = 720

        self.root.geometry(f"{self.window_width}x{self.window_height}")

        self.root.resizable(False, False)

        self.load_data()
        self.build_interface()
        self.position_near_tray()

        # Фоновое обновление информации на завтра
        self.root.after(
            self.TOMORROW_REFRESH_MS,
            self.refresh_tomorrow_data,
        )

    def load_data(self):
        """Загружает данные за сегодня и завтра."""

        try:
            self.today_prices = elering.get_today_hourly_prices()

            self.today_stats = elering.get_day_stats(self.today_prices)

        except Exception:
            self.today_prices = []
            self.today_stats = None

        self.load_tomorrow_data()

    def load_tomorrow_data(self):
        """Получает все доступные данные на завтра."""

        try:
            self.tomorrow_prices = elering.get_tomorrow_hourly_prices()

            self.tomorrow_stats = elering.get_day_stats(self.tomorrow_prices)

        except Exception:
            self.tomorrow_prices = []
            self.tomorrow_stats = None

    def build_interface(self):
        """Создаёт интерфейс панели."""

        title = tk.Label(
            self.root,
            text="ELECTRICITY · ESTONIA",
            font=("Arial", 13, "bold"),
        )

        title.pack(pady=(12, 4))

        self.current_label = tk.Label(
            self.root,
            text=f"{self.current_price:.2f} c/kWh",
            font=("Arial", 28, "bold"),
        )

        self.current_label.pack()

        current_description = tk.Label(
            self.root,
            text="текущая биржевая цена",
            font=("Arial", 9),
        )

        current_description.pack()

        self.interval_label = tk.Label(
            self.root,
            text=self.get_interval_text(),
            font=("Arial", 9),
        )

        self.interval_label.pack(pady=(6, 2))

        self.next_label = tk.Label(
            self.root,
            text=self.get_next_price_text(),
            font=("Arial", 10),
        )

        self.next_label.pack(pady=(0, 8))

        self.create_separator()

        # ---------- СЕГОДНЯ ----------

        today_title = tk.Label(
            self.root,
            text="Сегодня",
            font=("Arial", 11, "bold"),
        )

        today_title.pack(pady=(4, 2))

        self.today_stats_label = tk.Label(
            self.root,
            text=self.get_today_stats_text(),
            font=("Arial", 9),
            justify="center",
        )

        self.today_stats_label.pack(pady=(0, 6))

        self.today_canvas = tk.Canvas(
            self.root,
            width=390,
            height=180,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )

        self.today_canvas.pack(pady=(2, 8))

        self.draw_chart(
            self.today_canvas,
            self.today_prices,
        )

        self.create_separator()

        # ---------- ЗАВТРА ----------

        tomorrow_title = tk.Label(
            self.root,
            text="Завтра",
            font=("Arial", 11, "bold"),
        )

        tomorrow_title.pack(pady=(4, 2))

        self.tomorrow_stats_label = tk.Label(
            self.root,
            text=self.get_tomorrow_stats_text(),
            font=("Arial", 9),
            justify="center",
        )

        self.tomorrow_stats_label.pack(pady=(0, 6))

        self.tomorrow_canvas = tk.Canvas(
            self.root,
            width=390,
            height=180,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )

        self.tomorrow_canvas.pack(pady=(2, 8))

        self.draw_chart(
            self.tomorrow_canvas,
            self.tomorrow_prices,
        )

        self.tomorrow_update_label = tk.Label(
            self.root,
            text=self.get_update_status_text(),
            font=("Arial", 8),
        )

        self.tomorrow_update_label.pack(pady=(0, 4))

        close_button = tk.Button(
            self.root,
            text="Закрыть",
            command=self.root.destroy,
            width=12,
        )

        close_button.pack(pady=(4, 8))

    def get_interval_text(self):
        """Возвращает текущий 15-минутный интервал."""

        now = datetime.now()

        interval_minute = (now.minute // 15) * 15

        return "Текущий интервал: " f"{now.hour:02d}:" f"{interval_minute:02d}"

    def get_next_price_text(self):
        """Текст следующей 15-минутной цены."""

        if self.next_price is None:
            return "Следующая цена недоступна"

        return f"Следующие 15 мин: " f"{self.next_price:.2f} c/kWh"

    def get_today_stats_text(self):
        """Статистика сегодняшнего дня."""

        if not self.today_stats:
            return "Данные недоступны"

        return (
            f"Мин: "
            f"{self.today_stats['minimum']:.2f} "
            f"c/kWh в "
            f"{self.today_stats['minimum_time']}"
            f"   |   "
            f"Макс: "
            f"{self.today_stats['maximum']:.2f} "
            f"c/kWh в "
            f"{self.today_stats['maximum_time']}\n"
            f"Средняя: "
            f"{self.today_stats['average']:.2f} "
            f"c/kWh"
        )

    def get_tomorrow_stats_text(self):
        """Показывает любые уже опубликованные данные завтра."""

        count = len(self.tomorrow_prices)

        if count == 0:
            return "Цены на завтра " "ещё не опубликованы"

        if not self.tomorrow_stats:
            return f"Опубликовано часов: {count}"

        return (
            f"Опубликовано часов: {count} из 24\n"
            f"Мин: "
            f"{self.tomorrow_stats['minimum']:.2f} "
            f"c/kWh в "
            f"{self.tomorrow_stats['minimum_time']}"
            f"   |   "
            f"Макс: "
            f"{self.tomorrow_stats['maximum']:.2f} "
            f"c/kWh в "
            f"{self.tomorrow_stats['maximum_time']}\n"
            f"Средняя опубликованных: "
            f"{self.tomorrow_stats['average']:.2f} "
            f"c/kWh"
        )

    def get_update_status_text(self):
        """Время последней проверки завтра."""

        now = datetime.now()

        return (
            "Последняя проверка завтра: "
            f"{now:%H:%M:%S}   "
            "· обновление каждые 15 мин"
        )

    def refresh_tomorrow_data(self):
        """
        Каждые 15 минут запрашивает
        данные следующего дня.
        """

        old_count = len(self.tomorrow_prices)

        self.load_tomorrow_data()

        new_count = len(self.tomorrow_prices)

        self.tomorrow_stats_label.config(text=self.get_tomorrow_stats_text())

        self.tomorrow_update_label.config(text=self.get_update_status_text())

        # График перерисовываем всегда.
        self.tomorrow_canvas.delete("all")

        self.draw_chart(
            self.tomorrow_canvas,
            self.tomorrow_prices,
        )

        # Если появились новые значения,
        # временно отражаем это в заголовке окна.
        if new_count > old_count:
            self.root.title(
                f"Electricity Estonia " f"— завтра +{new_count - old_count}"
            )
        else:
            self.root.title("Electricity Estonia")

        # Планируем следующую проверку
        self.root.after(
            self.TOMORROW_REFRESH_MS,
            self.refresh_tomorrow_data,
        )

    def create_separator(self):
        """Горизонтальный разделитель."""

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

    def draw_chart(
        self,
        canvas,
        prices,
    ):
        """Рисует график опубликованных почасовых цен."""

        canvas.delete("all")

        if not prices:

            canvas.create_text(
                195,
                90,
                text="Данных пока нет",
                font=("Arial", 10),
            )

            return

        values = [item["cents_kwh"] for item in prices]

        max_value = max(values)

        if max_value <= 0:
            max_value = 1

        chart_left = 30
        chart_top = 15
        chart_width = 340
        chart_height = 130

        # Оси

        canvas.create_line(
            chart_left,
            chart_top + chart_height,
            chart_left + chart_width,
            chart_top + chart_height,
        )

        canvas.create_line(
            chart_left,
            chart_top,
            chart_left,
            chart_top + chart_height,
        )

        count = len(values)

        # Один опубликованный час —
        # показываем отдельной точкой
        if count == 1:

            x = chart_left

            y = chart_top + chart_height - (values[0] / max_value) * chart_height

            canvas.create_oval(
                x - 3,
                y - 3,
                x + 3,
                y + 3,
                fill="black",
            )

        else:

            points = []

            # Используем положение часа
            # на полной 24-часовой шкале,
            # а не растягиваем неполные данные.
            for item in prices:

                hour = item["time"].hour
                value = item["cents_kwh"]

                x = chart_left + (hour / 23) * chart_width

                y = chart_top + chart_height - (value / max_value) * chart_height

                points.extend(
                    [
                        x,
                        y,
                    ]
                )

            canvas.create_line(
                points,
                width=2,
                smooth=True,
            )

        # Шкала времени всегда полные сутки

        for hour in [
            0,
            6,
            12,
            18,
            23,
        ]:

            x = chart_left + (hour / 23) * chart_width

            canvas.create_text(
                x,
                chart_top + chart_height + 15,
                text=f"{hour:02d}",
                font=("Arial", 8),
            )

        canvas.create_text(
            5,
            chart_top,
            text=f"{max_value:.1f}",
            anchor="w",
            font=("Arial", 8),
        )

        canvas.create_text(
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
        """Размещает окно над панелью задач."""

        self.root.update_idletasks()

        try:

            work_area = self.get_work_area()

            x = work_area.right - self.window_width - 10

            y = work_area.bottom - self.window_height - 10

            if y < work_area.top:
                y = work_area.top + 10

        except Exception:

            screen_width = self.root.winfo_screenwidth()

            screen_height = self.root.winfo_screenheight()

            x = screen_width - self.window_width - 10

            y = max(
                10,
                screen_height - self.window_height - 60,
            )

        self.root.geometry(f"{self.window_width}x" f"{self.window_height}" f"+{x}+{y}")

    def run(self):
        self.root.mainloop()
