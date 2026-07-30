import ctypes
import math
import tkinter as tk
from datetime import datetime, timedelta

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

        self.window_width = 820
        self.window_height = 680

        self.root.geometry(f"{self.window_width}x{self.window_height}")

        self.root.resizable(False, False)

        self.load_data()
        self.build_interface()
        self.position_near_tray()

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

        title.pack(pady=(8, 2))

        self.current_label = tk.Label(
            self.root,
            text=f"{self.current_price:.2f} c/kWh",
            font=("Arial", 26, "bold"),
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

        self.interval_label.pack(pady=(4, 1))

        self.next_label = tk.Label(
            self.root,
            text=self.get_next_price_text(),
            font=("Arial", 10),
        )

        self.next_label.pack(pady=(0, 5))

        self.create_separator()

        # ---------------- Сегодня ----------------

        today_date = datetime.now().date()

        today_title = tk.Label(
            self.root,
            text=f"Сегодня — {today_date:%d.%m.%Y}",
            font=("Arial", 11, "bold"),
        )

        today_title.pack(pady=(2, 1))

        self.today_stats_label = tk.Label(
            self.root,
            text=self.get_today_stats_text(),
            font=("Arial", 9),
            justify="center",
        )

        self.today_stats_label.pack(pady=(0, 3))

        self.today_canvas = tk.Canvas(
            self.root,
            width=780,
            height=190,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )

        self.today_canvas.pack(pady=(1, 5))

        self.draw_chart(
            self.today_canvas,
            self.today_prices,
            show_current_time=True,
        )

        self.enable_hover(
            self.today_canvas,
            self.today_prices,
        )

        self.create_separator()

        # ---------------- Завтра ----------------

        tomorrow_date = datetime.now().date() + timedelta(days=1)

        tomorrow_title = tk.Label(
            self.root,
            text=f"Завтра — {tomorrow_date:%d.%m.%Y}",
            font=("Arial", 11, "bold"),
        )

        tomorrow_title.pack(pady=(2, 1))

        self.tomorrow_stats_label = tk.Label(
            self.root,
            text=self.get_tomorrow_stats_text(),
            font=("Arial", 9),
            justify="center",
        )

        self.tomorrow_stats_label.pack(pady=(0, 3))

        self.tomorrow_canvas = tk.Canvas(
            self.root,
            width=780,
            height=190,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )

        self.tomorrow_canvas.pack(pady=(1, 4))

        self.draw_chart(
            self.tomorrow_canvas,
            self.tomorrow_prices,
            show_current_time=False,
        )

        self.enable_hover(
            self.tomorrow_canvas,
            self.tomorrow_prices,
        )

        self.tomorrow_update_label = tk.Label(
            self.root,
            text=self.get_update_status_text(),
            font=("Arial", 8),
        )

        self.tomorrow_update_label.pack(pady=(0, 2))

        close_button = tk.Button(
            self.root,
            text="Закрыть",
            command=self.root.destroy,
            width=12,
        )

        close_button.pack(pady=(2, 5))

    def get_interval_text(self):
        """Возвращает текущий 15-минутный интервал."""

        now = datetime.now()

        start_minute = (now.minute // 15) * 15

        start = now.replace(
            minute=start_minute,
            second=0,
            microsecond=0,
        )

        end = start + timedelta(minutes=15)

        return "Текущий интервал: " f"{start:%H:%M}–{end:%H:%M}"

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
            f"{self.today_stats['maximum_time']}"
            f"   |   "
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
            f"Опубликовано часов: {count} из 24"
            f"   |   "
            f"Мин: "
            f"{self.tomorrow_stats['minimum']:.2f} "
            f"c/kWh в "
            f"{self.tomorrow_stats['minimum_time']}"
            f"   |   "
            f"Макс: "
            f"{self.tomorrow_stats['maximum']:.2f} "
            f"c/kWh в "
            f"{self.tomorrow_stats['maximum_time']}"
            f"   |   "
            f"Средняя: "
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
        """Обновляет данные на завтра."""

        self.load_tomorrow_data()

        self.tomorrow_stats_label.config(text=self.get_tomorrow_stats_text())

        self.tomorrow_update_label.config(text=self.get_update_status_text())

        self.draw_chart(
            self.tomorrow_canvas,
            self.tomorrow_prices,
            show_current_time=False,
        )

        self.enable_hover(
            self.tomorrow_canvas,
            self.tomorrow_prices,
        )

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
            pady=2,
        )

    def calculate_y_scale(self, values):
        """
        Адаптивно рассчитывает верхнюю границу шкалы Y.
        """

        if not values:
            return 1.0

        max_value = max(values)

        if max_value <= 0:
            return 1.0

        # Добавляем запас примерно 10 %
        target = max_value * 1.10

        magnitude = 10 ** math.floor(math.log10(target))

        normalized = target / magnitude

        if normalized <= 1:
            nice = 1

        elif normalized <= 2:
            nice = 2

        elif normalized <= 5:
            nice = 5

        else:
            nice = 10

        return nice * magnitude

    def draw_chart(
        self,
        canvas,
        prices,
        show_current_time=False,
    ):
        """Рисует ступенчатый график почасовых цен."""

        canvas.delete("all")

        canvas.chart_prices = prices

        chart_left = 42
        chart_top = 16
        chart_width = 720
        chart_height = 135

        if not prices:

            canvas.create_text(
                390,
                90,
                text="Данных пока нет",
                font=("Arial", 10),
            )

            return

        values = [item["cents_kwh"] for item in prices]

        y_max = self.calculate_y_scale(values)

        canvas.chart_geometry = {
            "left": chart_left,
            "top": chart_top,
            "width": chart_width,
            "height": chart_height,
            "y_max": y_max,
        }

        # Вертикальная сетка 00–24
        for hour in range(25):

            x = chart_left + (hour / 24) * chart_width

            canvas.create_line(
                x,
                chart_top,
                x,
                chart_top + chart_height,
                fill="#dddddd",
                dash=(2, 2),
            )

            canvas.create_text(
                x,
                chart_top + chart_height + 16,
                text=f"{hour:02d}",
                font=("Arial", 7),
            )

        # Горизонтальная сетка
        y_steps = 4

        for step in range(y_steps + 1):

            value = y_max * step / y_steps

            y = chart_top + chart_height - (value / y_max) * chart_height

            canvas.create_line(
                chart_left,
                y,
                chart_left + chart_width,
                y,
                fill="#eeeeee",
            )

            canvas.create_text(
                5,
                y,
                text=f"{value:.1f}",
                anchor="w",
                font=("Arial", 8),
            )

        # Оси
        canvas.create_line(
            chart_left,
            chart_top,
            chart_left,
            chart_top + chart_height,
            width=1,
        )

        canvas.create_line(
            chart_left,
            chart_top + chart_height,
            chart_left + chart_width,
            chart_top + chart_height,
            width=1,
        )

        # Подпись Y
        canvas.create_text(
            6,
            5,
            text="c/kWh",
            anchor="w",
            font=("Arial", 8),
        )

        # Ступенчатый график
        points = []

        for item in prices:

            hour = item["time"].hour
            value = item["cents_kwh"]

            x_start = chart_left + (hour / 24) * chart_width

            x_end = chart_left + ((hour + 1) / 24) * chart_width

            y = chart_top + chart_height - (value / y_max) * chart_height

            if not points:
                points.extend(
                    [
                        x_start,
                        y,
                    ]
                )

            points.extend(
                [
                    x_end,
                    y,
                ]
            )

            next_hour = hour + 1

            next_item = None

            for candidate in prices:
                if candidate["time"].hour == next_hour:
                    next_item = candidate
                    break

            if next_item is not None:

                next_y = (
                    chart_top
                    + chart_height
                    - (next_item["cents_kwh"] / y_max) * chart_height
                )

                points.extend(
                    [
                        x_end,
                        next_y,
                    ]
                )

        if len(points) >= 4:
            canvas.create_line(
                points,
                width=2,
            )

        # Текущее время
        if show_current_time:

            now = datetime.now()

            seconds_today = now.hour * 3600 + now.minute * 60 + now.second

            day_fraction = seconds_today / (24 * 3600)

            current_x = chart_left + day_fraction * chart_width

            canvas.create_line(
                current_x,
                chart_top,
                current_x,
                chart_top + chart_height,
                width=2,
                dash=(4, 3),
            )

            canvas.create_text(
                current_x,
                chart_top + 5,
                text=f"{now:%H:%M}",
                anchor="n",
                font=("Arial", 8, "bold"),
            )

    def enable_hover(
        self,
        canvas,
        prices,
    ):
        """Подключает всплывающую подсказку над графиком."""

        canvas.chart_prices = prices

        canvas.bind(
            "<Motion>",
            lambda event: self.on_chart_motion(
                event,
                canvas,
            ),
        )

        canvas.bind(
            "<Leave>",
            lambda event: self.hide_chart_tooltip(canvas),
        )

    def on_chart_motion(
        self,
        event,
        canvas,
    ):
        """Обрабатывает движение мыши по графику."""

        if not hasattr(
            canvas,
            "chart_geometry",
        ):
            return

        geometry = canvas.chart_geometry

        chart_left = geometry["left"]

        chart_width = geometry["width"]

        chart_top = geometry["top"]

        chart_height = geometry["height"]

        x = event.x

        if x < chart_left or x > chart_left + chart_width:
            self.hide_chart_tooltip(canvas)
            return

        fraction = (x - chart_left) / chart_width

        hour = int(fraction * 24)

        hour = max(
            0,
            min(
                23,
                hour,
            ),
        )

        item = None

        for price_item in canvas.chart_prices:
            if price_item["time"].hour == hour:
                item = price_item
                break

        if item is None:
            self.hide_chart_tooltip(canvas)
            return

        value = item["cents_kwh"]

        vat_value = item.get("cents_kwh_vat")

        y_max = geometry["y_max"]

        item_y = chart_top + chart_height - (value / y_max) * chart_height

        hour_x = chart_left + ((hour + 0.5) / 24) * chart_width

        canvas.delete("hover")

        # Вертикальная линия выбранного часа
        canvas.create_line(
            hour_x,
            chart_top,
            hour_x,
            chart_top + chart_height,
            fill="#777777",
            dash=(2, 2),
            tags="hover",
        )

        # Точка цены
        canvas.create_oval(
            hour_x - 4,
            item_y - 4,
            hour_x + 4,
            item_y + 4,
            fill="black",
            tags="hover",
        )

        end_hour = hour + 1

        tooltip_text = f"{hour:02d}:00–" f"{end_hour:02d}:00\n" f"{value:.3f} c/kWh"

        if vat_value is not None:
            tooltip_text += f"\nс НДС: " f"{vat_value:.3f} c/kWh"

        tooltip_x = event.x + 12

        tooltip_y = event.y - 12

        # Не даём tooltip выйти вправо
        if tooltip_x > 610:
            tooltip_x = event.x - 150

        # Не даём выйти вверх
        if tooltip_y < 30:
            tooltip_y = event.y + 20

        text_id = canvas.create_text(
            tooltip_x,
            tooltip_y,
            text=tooltip_text,
            anchor="nw",
            font=("Arial", 9, "bold"),
            tags="hover",
        )

        bbox = canvas.bbox(text_id)

        if bbox:

            padding = 5

            rect_id = canvas.create_rectangle(
                bbox[0] - padding,
                bbox[1] - padding,
                bbox[2] + padding,
                bbox[3] + padding,
                fill="white",
                outline="black",
                tags="hover",
            )

            canvas.tag_lower(
                rect_id,
                text_id,
            )

    def hide_chart_tooltip(
        self,
        canvas,
    ):
        """Удаляет hover-подсказку."""

        canvas.delete("hover")

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
        """Размещает окно над taskbar."""

        self.root.update_idletasks()

        try:

            work_area = self.get_work_area()

            x = work_area.right - self.window_width - 10

            # Чуть больший запас снизу,
            # чтобы нижняя шкала точно была видна.
            margin_bottom = 18

            y = work_area.bottom - self.window_height - margin_bottom

            if y < work_area.top:
                y = work_area.top + 5

        except Exception:

            screen_width = self.root.winfo_screenwidth()

            screen_height = self.root.winfo_screenheight()

            x = screen_width - self.window_width - 10

            y = max(
                5,
                screen_height - self.window_height - 80,
            )

        self.root.geometry(f"{self.window_width}x" f"{self.window_height}" f"+{x}+{y}")

    def run(self):
        self.root.mainloop()
