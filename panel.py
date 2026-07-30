import ctypes
import math
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk

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

        self.table_visible = False

        self.root = tk.Tk()
        self.root.title("Electricity Estonia")

        self.window_width = 980

        # Высота обычного режима
        self.compact_height = 690

        # Желаемая высота режима с таблицей.
        # Фактическая высота будет ограничена
        # рабочей областью Windows.
        self.expanded_height = 920

        self.window_height = self.compact_height

        self.root.resizable(
            False,
            False,
        )

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
        """Создаёт основной интерфейс."""

        top_frame = tk.Frame(self.root)

        top_frame.pack(
            fill="x",
            pady=(6, 0),
        )

        title = tk.Label(
            top_frame,
            text="ELECTRICITY · ESTONIA",
            font=("Arial", 13, "bold"),
        )

        title.pack()

        # Кнопка таблицы
        self.table_button = tk.Button(
            self.root,
            text="Показать таблицу",
            command=self.toggle_table,
            width=18,
        )

        self.table_button.place(
            x=self.window_width - 165,
            y=12,
        )

        # Текущая цена
        self.current_label = tk.Label(
            self.root,
            text=(f"{self.current_price:.2f} " f"c/kWh"),
            font=("Arial", 26, "bold"),
        )

        self.current_label.pack()

        tk.Label(
            self.root,
            text="текущая биржевая цена",
            font=("Arial", 9),
        ).pack()

        self.interval_label = tk.Label(
            self.root,
            text=self.get_interval_text(),
            font=("Arial", 9),
        )

        self.interval_label.pack(pady=(3, 1))

        self.next_label = tk.Label(
            self.root,
            text=self.get_next_price_text(),
            font=("Arial", 10),
        )

        self.next_label.pack(pady=(0, 4))

        self.create_separator()

        # ======================================
        # СЕГОДНЯ
        # ======================================

        today_date = datetime.now().date()

        tk.Label(
            self.root,
            text=(f"Сегодня — " f"{today_date:%d.%m.%Y}"),
            font=("Arial", 11, "bold"),
        ).pack(pady=(2, 1))

        self.today_stats_label = tk.Label(
            self.root,
            text=self.get_today_stats_text(),
            font=("Arial", 9),
        )

        self.today_stats_label.pack(pady=(0, 2))

        self.today_canvas = tk.Canvas(
            self.root,
            width=940,
            height=195,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )

        self.today_canvas.pack(pady=(1, 4))

        self.draw_15min_chart(
            self.today_canvas,
            self.today_prices,
            show_current_time=True,
        )

        self.enable_hover(
            self.today_canvas,
            self.today_prices,
        )

        self.create_separator()

        # ======================================
        # ЗАВТРА
        # ======================================

        tomorrow_date = today_date + timedelta(days=1)

        tk.Label(
            self.root,
            text=(f"Завтра — " f"{tomorrow_date:%d.%m.%Y}"),
            font=("Arial", 11, "bold"),
        ).pack(pady=(2, 1))

        self.tomorrow_stats_label = tk.Label(
            self.root,
            text=self.get_tomorrow_stats_text(),
            font=("Arial", 9),
        )

        self.tomorrow_stats_label.pack(pady=(0, 2))

        self.tomorrow_canvas = tk.Canvas(
            self.root,
            width=940,
            height=195,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )

        self.tomorrow_canvas.pack(pady=(1, 3))

        self.draw_15min_chart(
            self.tomorrow_canvas,
            self.tomorrow_prices,
            show_current_time=False,
        )

        self.enable_hover(
            self.tomorrow_canvas,
            self.tomorrow_prices,
        )

        # Информация об обновлении
        self.tomorrow_update_label = tk.Label(
            self.root,
            text=(self.get_update_status_text()),
            font=("Arial", 8),
        )

        self.tomorrow_update_label.pack(pady=(0, 3))

        # Контейнер таблиц.
        # Изначально скрыт.
        self.table_frame = tk.Frame(self.root)

        # Отдельной кнопки "Закрыть" больше нет.
        # Используем стандартный X окна Windows.

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

    def get_interval_text(self):
        """Текущий 15-минутный интервал."""

        now = datetime.now()

        minute = (now.minute // 15) * 15

        start = now.replace(
            minute=minute,
            second=0,
            microsecond=0,
        )

        end = start + timedelta(minutes=15)

        return "Текущий интервал: " f"{start:%H:%M}–" f"{end:%H:%M}"

    def get_next_price_text(self):
        """Цена следующего интервала."""

        if self.next_price is None:
            return "Следующая цена недоступна"

        return "Следующие 15 мин: " f"{self.next_price:.2f} " "c/kWh"

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
        """Статистика доступных данных завтра."""

        count = len(self.tomorrow_prices)

        if count == 0:
            return "Цены на завтра " "ещё не опубликованы"

        percent = count / 96 * 100

        if not self.tomorrow_stats:
            return f"Опубликовано интервалов: " f"{count} из 96 " f"({percent:.1f}%)"

        return (
            f"Опубликовано интервалов: "
            f"{count} из 96 "
            f"({percent:.1f}%)"
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
            f"{now:%H:%M:%S}"
            "   ·   "
            "обновление каждые 15 мин"
        )

    def calculate_y_scale(
        self,
        values,
    ):
        """Адаптивный масштаб вертикальной оси."""

        if not values:
            return 1.0

        max_value = max(values)

        if max_value <= 0:
            return 1.0

        # Запас сверху
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

    def draw_15min_chart(
        self,
        canvas,
        prices,
        show_current_time=False,
    ):
        """Рисует 15-минутную столбчатую диаграмму."""

        canvas.delete("all")

        chart_left = 50
        chart_top = 18
        chart_width = 860
        chart_height = 135

        canvas.chart_prices = prices

        if not prices:
            canvas.create_text(
                470,
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

        # Вертикальная сетка по часам
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
                chart_top + chart_height + 18,
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
                6,
                y,
                text=f"{value:.1f}",
                anchor="w",
                font=("Arial", 8),
            )

        canvas.create_text(
            6,
            5,
            text="c/kWh",
            anchor="w",
            font=("Arial", 8),
        )

        # 96 интервалов в сутках
        bar_width = chart_width / 96

        for item in prices:

            hour = item["time"].hour

            minute = item["time"].minute

            index = hour * 4 + minute // 15

            x1 = chart_left + index * bar_width + 1

            x2 = chart_left + (index + 1) * bar_width - 1

            value = item["cents_kwh"]

            y = chart_top + chart_height - (value / y_max) * chart_height

            canvas.create_rectangle(
                x1,
                y,
                x2,
                chart_top + chart_height,
                fill="#4aa9df",
                outline="#188cca",
            )

        # Маркер текущего времени
        if show_current_time:

            now = datetime.now()

            seconds_today = now.hour * 3600 + now.minute * 60 + now.second

            fraction = seconds_today / 86400

            x = chart_left + fraction * chart_width

            canvas.create_line(
                x,
                chart_top,
                x,
                chart_top + chart_height,
                fill="red",
                width=2,
            )

            canvas.create_text(
                x,
                chart_top + 5,
                text=f"{now:%H:%M}",
                fill="red",
                anchor="n",
                font=(
                    "Arial",
                    8,
                    "bold",
                ),
            )

    def enable_hover(
        self,
        canvas,
        prices,
    ):
        """Включает hover по графику."""

        canvas.chart_prices = prices

        canvas.bind(
            "<Motion>",
            lambda event: (
                self.on_chart_motion(
                    event,
                    canvas,
                )
            ),
        )

        canvas.bind(
            "<Leave>",
            lambda event: (canvas.delete("hover")),
        )

    def on_chart_motion(
        self,
        event,
        canvas,
    ):
        """Показывает цену под указателем мыши."""

        if not hasattr(
            canvas,
            "chart_geometry",
        ):
            return

        geometry = canvas.chart_geometry

        left = geometry["left"]
        width = geometry["width"]
        top = geometry["top"]
        height = geometry["height"]
        y_max = geometry["y_max"]

        if event.x < left or event.x > left + width:
            canvas.delete("hover")
            return

        fraction = (event.x - left) / width

        index = int(fraction * 96)

        index = max(
            0,
            min(
                95,
                index,
            ),
        )

        hour = index // 4

        minute = (index % 4) * 15

        item = None

        for candidate in canvas.chart_prices:

            if candidate["time"].hour == hour and candidate["time"].minute == minute:
                item = candidate
                break

        if item is None:
            canvas.delete("hover")
            return

        value = item["cents_kwh"]

        vat_value = item.get("cents_kwh_vat")

        bar_width = width / 96

        center_x = left + (index + 0.5) * bar_width

        point_y = top + height - (value / y_max) * height

        canvas.delete("hover")

        # Точка выбранной цены
        canvas.create_oval(
            center_x - 4,
            point_y - 4,
            center_x + 4,
            point_y + 4,
            fill="black",
            tags="hover",
        )

        tooltip = f"{item['interval_text']}\n" f"{value:.3f} c/kWh"

        if vat_value is not None:

            tooltip += "\nс НДС: " f"{vat_value:.3f} " "c/kWh"

        tx = event.x + 12

        ty = event.y - 15

        if tx > 750:
            tx = event.x - 145

        if ty < 30:
            ty = event.y + 20

        text_id = canvas.create_text(
            tx,
            ty,
            text=tooltip,
            anchor="nw",
            font=(
                "Arial",
                9,
                "bold",
            ),
            tags="hover",
        )

        bbox = canvas.bbox(text_id)

        if bbox:

            rect_id = canvas.create_rectangle(
                bbox[0] - 5,
                bbox[1] - 5,
                bbox[2] + 5,
                bbox[3] + 5,
                fill="white",
                outline="black",
                tags="hover",
            )

            canvas.tag_lower(
                rect_id,
                text_id,
            )

    def toggle_table(self):
        """Показывает или скрывает таблицу."""

        if self.table_visible:

            self.table_frame.pack_forget()

            self.table_button.config(text="Показать таблицу")

            self.table_visible = False

            self.window_height = self.compact_height

        else:

            self.build_table()

            self.table_frame.pack(
                fill="both",
                expand=True,
                padx=15,
                pady=(2, 6),
            )

            self.table_button.config(text="Скрыть таблицу")

            self.table_visible = True

            self.window_height = self.expanded_height

        # position_near_tray сам ограничит
        # высоту рабочей областью Windows.
        self.position_near_tray()

    def build_table(self):
        """Создаёт таблицы сегодня/завтра."""

        for child in self.table_frame.winfo_children():
            child.destroy()

        container = tk.Frame(self.table_frame)

        container.pack(
            fill="both",
            expand=True,
        )

        left_frame = tk.Frame(container)

        left_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 5),
        )

        right_frame = tk.Frame(container)

        right_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(5, 0),
        )

        today_date = datetime.now().date()

        tomorrow_date = today_date + timedelta(days=1)

        self.create_price_table(
            left_frame,
            (f"Сегодня — " f"{today_date:%d.%m.%Y}"),
            self.today_prices,
        )

        self.create_price_table(
            right_frame,
            (
                f"Завтра — "
                f"{tomorrow_date:%d.%m.%Y} "
                f"("
                f"{len(self.tomorrow_prices)}"
                f" из 96)"
            ),
            self.tomorrow_prices,
        )

    def create_price_table(
        self,
        parent,
        title,
        prices,
    ):
        """Создаёт таблицу одного дня."""

        tk.Label(
            parent,
            text=title,
            font=(
                "Arial",
                9,
                "bold",
            ),
        ).pack()

        columns = (
            "interval",
            "price",
            "vat",
        )

        tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=9,
        )

        tree.heading(
            "interval",
            text="Интервал",
        )

        tree.heading(
            "price",
            text="Цена, c/kWh",
        )

        tree.heading(
            "vat",
            text="С НДС, c/kWh",
        )

        tree.column(
            "interval",
            width=140,
            anchor="center",
        )

        tree.column(
            "price",
            width=110,
            anchor="center",
        )

        tree.column(
            "vat",
            width=110,
            anchor="center",
        )

        scrollbar = ttk.Scrollbar(
            parent,
            orient="vertical",
            command=tree.yview,
        )

        tree.configure(yscrollcommand=(scrollbar.set))

        tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        now = datetime.now()

        current_index = now.hour * 4 + now.minute // 15

        for item in prices:

            tag = ""

            item_index = item["time"].hour * 4 + item["time"].minute // 15

            if item["date"] == now.date() and item_index == current_index:
                tag = "current"

            tree.insert(
                "",
                "end",
                values=(
                    item["interval_text"],
                    (f"{item['cents_kwh']:.3f}"),
                    (f"{item['cents_kwh_vat']:.3f}"),
                ),
                tags=(tag,),
            )

        # Текущий интервал
        tree.tag_configure(
            "current",
            background="#fff4a8",
        )

    def refresh_tomorrow_data(self):
        """Периодическое обновление завтра."""

        self.load_tomorrow_data()

        self.tomorrow_stats_label.config(text=(self.get_tomorrow_stats_text()))

        self.tomorrow_update_label.config(text=(self.get_update_status_text()))

        self.draw_15min_chart(
            self.tomorrow_canvas,
            self.tomorrow_prices,
            show_current_time=False,
        )

        self.enable_hover(
            self.tomorrow_canvas,
            self.tomorrow_prices,
        )

        if self.table_visible:
            self.build_table()

        self.root.after(
            self.TOMORROW_REFRESH_MS,
            self.refresh_tomorrow_data,
        )

    def get_work_area(self):
        """Получает реальную рабочую область Windows."""

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
        """
        Размещает панель над taskbar.

        В режиме таблицы автоматически
        ограничивает высоту рабочей областью
        и поднимает окно вверх.
        """

        self.root.update_idletasks()

        try:

            area = self.get_work_area()

            work_width = area.right - area.left

            work_height = area.bottom - area.top

            # Небольшой безопасный отступ
            margin = 8

            # Не позволяем окну быть выше
            # доступной рабочей области.
            actual_height = min(
                self.window_height,
                work_height - margin * 2,
            )

            actual_width = min(
                self.window_width,
                work_width - margin * 2,
            )

            # Прижимаем к правому краю.
            x = area.right - actual_width - margin

            if self.table_visible:

                # В раскрытом режиме окно
                # максимально поднимаем,
                # чтобы нижняя рамка и таблица
                # гарантированно были видны.
                y = area.top + margin

            else:

                # Обычный режим остаётся
                # возле панели задач.
                y = area.bottom - actual_height - margin

            self.root.geometry(f"{actual_width}x" f"{actual_height}" f"+{x}+{y}")

        except Exception:

            screen_width = self.root.winfo_screenwidth()

            screen_height = self.root.winfo_screenheight()

            margin = 8

            actual_height = min(
                self.window_height,
                screen_height - 80,
            )

            x = screen_width - self.window_width - margin

            if self.table_visible:
                y = margin

            else:
                y = max(
                    margin,
                    screen_height - actual_height - 60,
                )

            self.root.geometry(f"{self.window_width}x" f"{actual_height}" f"+{x}+{y}")

    def run(self):
        self.root.mainloop()
