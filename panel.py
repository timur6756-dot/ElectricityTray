import ctypes
import math
import tkinter as tk

from datetime import (
    datetime,
    timedelta,
)

from tkinter import ttk

import elering

from i18n import (
    LANGUAGE_SHORT,
    normalize_language,
    t,
)


class RECT(ctypes.Structure):

    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class PricePanel:

    def __init__(
        self,
        current_price,
        next_price,
        language="ru",
        language_getter=None,
        language_setter=None,
    ):

        self.current_price = current_price

        self.next_price = next_price

        self.language = normalize_language(language)

        self.language_getter = language_getter

        self.language_setter = language_setter

        self.today_prices = []
        self.today_stats = None

        self.tomorrow_prices = []
        self.tomorrow_stats = None

        self.table_visible = False

        self.root = tk.Tk()

        self.window_width = 980
        self.compact_height = 690
        self.expanded_height = 920

        self.window_height = self.compact_height

        self.root.resizable(
            False,
            False,
        )

        self.load_all_data()

        self.build_interface()

        self.apply_language()

        self.position_near_tray()

        self.schedule_next_market_update()

        # Проверяем изменение языка из tray.
        self.root.after(
            300,
            self.sync_language,
        )

    # ======================================================
    # DATA
    # ======================================================

    def load_all_data(self):

        try:

            current = elering.get_current_and_next_estonia_price()

            self.current_price = current["current"]["cents_kwh"]

            if current["next"] is not None:

                self.next_price = current["next"]["cents_kwh"]

            else:

                self.next_price = None

        except Exception:

            pass

        try:

            self.today_prices = elering.get_today_hourly_prices()

            self.today_stats = elering.get_day_stats(self.today_prices)

        except Exception:

            pass

        self.load_tomorrow_data()

    def load_tomorrow_data(self):

        try:

            self.tomorrow_prices = elering.get_tomorrow_hourly_prices()

            self.tomorrow_stats = elering.get_day_stats(self.tomorrow_prices)

        except Exception:

            pass

    # ======================================================
    # INTERFACE
    # ======================================================

    def build_interface(self):

        top_frame = tk.Frame(self.root)

        top_frame.pack(
            fill="x",
            pady=(6, 0),
        )

        self.title_label = tk.Label(
            top_frame,
            text="ELECTRICITY · ESTONIA",
            font=(
                "Arial",
                13,
                "bold",
            ),
        )

        self.title_label.pack()

        # ----------------------------------
        # Table button
        # ----------------------------------

        self.table_button = tk.Button(
            self.root,
            command=self.toggle_table,
            width=18,
        )

        self.table_button.place(
            x=self.window_width - 165,
            y=12,
        )

        # ----------------------------------
        # Language selector
        # directly below Table button
        # ----------------------------------

        self.language_var = tk.StringVar(value=(LANGUAGE_SHORT[self.language]))

        self.language_selector = ttk.Combobox(
            self.root,
            textvariable=(self.language_var),
            values=(
                "RU",
                "EN",
                "ET",
            ),
            state="readonly",
            width=5,
            justify="center",
        )

        self.language_selector.place(
            x=self.window_width - 105,
            y=45,
        )

        self.language_selector.bind(
            "<<ComboboxSelected>>",
            self.on_language_selected,
        )

        # ----------------------------------
        # Current price
        # ----------------------------------

        self.current_label = tk.Label(
            self.root,
            text="",
            font=(
                "Arial",
                26,
                "bold",
            ),
        )

        self.current_label.pack()

        self.current_description_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 9),
        )

        self.current_description_label.pack()

        self.interval_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 9),
        )

        self.interval_label.pack(pady=(3, 1))

        self.next_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 10),
        )

        self.next_label.pack(pady=(0, 4))

        self.create_separator()

        # ----------------------------------
        # Today
        # ----------------------------------

        self.today_title_label = tk.Label(
            self.root,
            text="",
            font=(
                "Arial",
                11,
                "bold",
            ),
        )

        self.today_title_label.pack(pady=(2, 1))

        self.today_stats_label = tk.Label(
            self.root,
            text="",
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

        self.create_separator()

        # ----------------------------------
        # Tomorrow
        # ----------------------------------

        self.tomorrow_title_label = tk.Label(
            self.root,
            text="",
            font=(
                "Arial",
                11,
                "bold",
            ),
        )

        self.tomorrow_title_label.pack(pady=(2, 1))

        self.tomorrow_stats_label = tk.Label(
            self.root,
            text="",
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

        self.update_status_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 8),
        )

        self.update_status_label.pack(pady=(0, 3))

        self.table_frame = tk.Frame(self.root)

    def create_separator(self):

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

    # ======================================================
    # LANGUAGE
    # ======================================================

    def on_language_selected(
        self,
        event=None,
    ):

        short = self.language_var.get().lower()

        mapping = {
            "ru": "ru",
            "en": "en",
            "et": "et",
        }

        language = mapping.get(
            short,
            "ru",
        )

        self.language = language

        if self.language_setter is not None:

            try:

                self.language_setter(language)

            except Exception:

                pass

        self.apply_language()

    def sync_language(self):
        """
        Подхватывает выбор,
        сделанный через tray menu.
        """

        try:

            if self.language_getter is not None:

                new_language = normalize_language(self.language_getter())

                if new_language != self.language:

                    self.language = new_language

                    self.apply_language()

        except Exception:

            pass

        try:

            self.root.after(
                300,
                self.sync_language,
            )

        except Exception:

            pass

    def apply_language(self):
        """Обновляет все локализуемые элементы."""

        self.root.title(
            t(
                "window_title",
                self.language,
            )
        )

        self.language_var.set(LANGUAGE_SHORT[self.language])

        if self.table_visible:

            self.table_button.config(
                text=t(
                    "hide_table",
                    self.language,
                )
            )

        else:

            self.table_button.config(
                text=t(
                    "show_table",
                    self.language,
                )
            )

        self.current_description_label.config(
            text=t(
                "current_exchange_price",
                self.language,
            )
        )

        self.update_text_labels()

        self.draw_15min_chart(
            self.today_canvas,
            self.today_prices,
            show_current_time=True,
        )

        self.enable_hover(
            self.today_canvas,
            self.today_prices,
        )

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

    # ======================================================
    # TEXT
    # ======================================================

    def get_today_title(self):

        today = datetime.now().date()

        return f"{t('today', self.language)}" f" — " f"{today:%d.%m.%Y}"

    def get_tomorrow_title(self):

        tomorrow = datetime.now().date() + timedelta(days=1)

        return f"{t('tomorrow', self.language)}" f" — " f"{tomorrow:%d.%m.%Y}"

    def get_interval_text(self):

        now = datetime.now()

        minute = (now.minute // 15) * 15

        start = now.replace(
            minute=minute,
            second=0,
            microsecond=0,
        )

        end = start + timedelta(minutes=15)

        return t(
            "current_interval",
            self.language,
            start=start.strftime("%H:%M"),
            end=end.strftime("%H:%M"),
        )

    def get_next_price_text(self):

        if self.next_price is None:

            return t(
                "next_unavailable",
                self.language,
            )

        return t(
            "next_15",
            self.language,
            price=self.next_price,
        )

    def get_today_stats_text(self):

        if not self.today_stats:

            return t(
                "data_unavailable",
                self.language,
            )

        return t(
            "today_stats",
            self.language,
            minimum=(self.today_stats["minimum"]),
            minimum_time=(self.today_stats["minimum_time"]),
            maximum=(self.today_stats["maximum"]),
            maximum_time=(self.today_stats["maximum_time"]),
            average=(self.today_stats["average"]),
        )

    def get_tomorrow_stats_text(self):

        count = len(self.tomorrow_prices)

        if count == 0:

            return t(
                "tomorrow_not_published",
                self.language,
            )

        percent = count / 96 * 100

        if not self.tomorrow_stats:

            return t(
                "tomorrow_intervals",
                self.language,
                count=count,
                percent=percent,
            )

        return t(
            "tomorrow_stats",
            self.language,
            count=count,
            percent=percent,
            minimum=(self.tomorrow_stats["minimum"]),
            minimum_time=(self.tomorrow_stats["minimum_time"]),
            maximum=(self.tomorrow_stats["maximum"]),
            maximum_time=(self.tomorrow_stats["maximum_time"]),
            average=(self.tomorrow_stats["average"]),
        )

    def get_update_status_text(self):

        return t(
            "last_update",
            self.language,
            time=(datetime.now().strftime("%H:%M:%S")),
        )

    def update_text_labels(self):

        self.current_label.config(text=(f"{self.current_price:.2f} " f"c/kWh"))

        self.interval_label.config(text=self.get_interval_text())

        self.next_label.config(text=self.get_next_price_text())

        self.today_title_label.config(text=self.get_today_title())

        self.tomorrow_title_label.config(text=self.get_tomorrow_title())

        self.today_stats_label.config(text=self.get_today_stats_text())

        self.tomorrow_stats_label.config(text=(self.get_tomorrow_stats_text()))

        self.update_status_label.config(text=(self.get_update_status_text()))

    # ======================================================
    # CHART
    # ======================================================

    def calculate_y_scale(
        self,
        values,
    ):

        if not values:
            return 1.0

        max_value = max(values)

        if max_value <= 0:
            return 1.0

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
                text=t(
                    "no_data",
                    self.language,
                ),
                font=(
                    "Arial",
                    10,
                ),
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

        # Hour grid
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
                font=(
                    "Arial",
                    7,
                ),
            )

        # Y grid
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
                font=(
                    "Arial",
                    8,
                ),
            )

        canvas.create_text(
            6,
            5,
            text="c/kWh",
            anchor="w",
            font=(
                "Arial",
                8,
            ),
        )

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

    # ======================================================
    # HOVER
    # ======================================================

    def enable_hover(
        self,
        canvas,
        prices,
    ):

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
            lambda event: canvas.delete("hover"),
        )

    def on_chart_motion(
        self,
        event,
        canvas,
    ):

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

            tooltip += "\n" f"{t('with_vat', self.language)}: " f"{vat_value:.3f} c/kWh"

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

    # ======================================================
    # TABLE
    # ======================================================

    def toggle_table(self):

        if self.table_visible:

            self.table_frame.pack_forget()

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

            self.table_visible = True

            self.window_height = self.expanded_height

        self.apply_language()

        self.position_near_tray()

    def build_table(self):

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

        today = datetime.now().date()

        tomorrow = today + timedelta(days=1)

        self.create_price_table(
            left_frame,
            (f"{t('today', self.language)}" f" — " f"{today:%d.%m.%Y}"),
            self.today_prices,
        )

        self.create_price_table(
            right_frame,
            (
                f"{t('tomorrow', self.language)}"
                f" — "
                f"{tomorrow:%d.%m.%Y}"
                f" "
                f"({len(self.tomorrow_prices)}/96)"
            ),
            self.tomorrow_prices,
        )

    def create_price_table(
        self,
        parent,
        title,
        prices,
    ):

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
            text=t(
                "interval",
                self.language,
            ),
        )

        tree.heading(
            "price",
            text=t(
                "price",
                self.language,
            ),
        )

        tree.heading(
            "vat",
            text=t(
                "price_vat",
                self.language,
            ),
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

        tree.tag_configure(
            "current",
            background="#fff4a8",
        )

    # ======================================================
    # LIVE UPDATE
    # ======================================================

    def refresh_all_data(self):

        try:

            current = elering.get_current_and_next_estonia_price()

            self.current_price = current["current"]["cents_kwh"]

            if current["next"] is not None:

                self.next_price = current["next"]["cents_kwh"]

            else:

                self.next_price = None

        except Exception:

            pass

        try:

            new_today = elering.get_today_hourly_prices()

            if new_today:

                self.today_prices = new_today

                self.today_stats = elering.get_day_stats(self.today_prices)

        except Exception:

            pass

        self.load_tomorrow_data()

        self.apply_language()

        self.schedule_next_market_update()

    def schedule_next_market_update(self):

        now = datetime.now()

        minute_block = (now.minute // 15) * 15

        current_boundary = now.replace(
            minute=minute_block,
            second=0,
            microsecond=0,
        )

        next_boundary = current_boundary + timedelta(minutes=15) + timedelta(seconds=5)

        delay_seconds = (next_boundary - now).total_seconds()

        delay_ms = max(
            1000,
            int(delay_seconds * 1000),
        )

        self.root.after(
            delay_ms,
            self.refresh_all_data,
        )

    # ======================================================
    # WINDOWS POSITION
    # ======================================================

    def get_work_area(self):

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

        self.root.update_idletasks()

        try:

            area = self.get_work_area()

            work_width = area.right - area.left

            work_height = area.bottom - area.top

            margin = 8

            actual_height = min(
                self.window_height,
                work_height - margin * 2,
            )

            actual_width = min(
                self.window_width,
                work_width - margin * 2,
            )

            x = area.right - actual_width - margin

            if self.table_visible:

                y = area.top + margin

            else:

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
