from PIL import Image, ImageDraw, ImageFont
import pystray
import threading
import time
from datetime import datetime

import elering
import config
from panel import PricePanel


class TrayIcon:

    def __init__(self):
        prices = elering.get_current_and_next_estonia_price()

        self.price = prices["current"]["cents_kwh"]

        if prices["next"] is not None:
            self.next_price = prices["next"]["cents_kwh"]
        else:
            self.next_price = None

        self.tomorrow_count = 0
        self.tomorrow_monitor_date = datetime.now().date()

        # -----------------------------
        # Управление единственной панелью
        # -----------------------------

        self.panel = None
        self.panel_open = False

        self.panel_lock = threading.Lock()

        # Сигнал существующему окну:
        # "покажись и выйди на передний план".
        self.show_panel_event = threading.Event()

        try:
            tomorrow = elering.get_tomorrow_hourly_prices()
            self.tomorrow_count = len(tomorrow)

        except Exception:
            self.tomorrow_count = 0

        self.icon = pystray.Icon(
            "ElectricityTray",
            self.create_icon(self.price),
            self.create_tooltip(),
            menu=pystray.Menu(
                pystray.MenuItem(
                    "Открыть панель",
                    self.open_panel,
                    default=True,
                ),
                pystray.MenuItem(
                    "Обновить",
                    self.refresh,
                ),
                pystray.MenuItem(
                    "Выход",
                    self.exit_program,
                ),
            ),
        )

        self.running = True

    # ==========================================================
    # ICON
    # ==========================================================

    def get_price_color(self, price):
        """Цвет молнии по текущей цене."""

        if price < config.PRICE_CHEAP:
            return "green"

        if price < config.PRICE_NORMAL:
            return "gold"

        if price < config.PRICE_EXPENSIVE:
            return "orange"

        return "red"

    def create_icon(self, price):
        """Создаёт значок tray."""

        image = Image.new(
            "RGB",
            (64, 64),
            "white",
        )

        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.truetype(
                "arialbd.ttf",
                34,
            )

        except OSError:
            font = ImageFont.load_default()

        price_text = f"{price:.1f}"

        bbox = draw.textbbox(
            (0, 0),
            price_text,
            font=font,
        )

        text_width = bbox[2] - bbox[0]

        x = (64 - text_width) // 2

        draw.text(
            (x, -5),
            price_text,
            font=font,
            fill="black",
        )

        lightning_color = self.get_price_color(price)

        draw.polygon(
            [
                (31, 34),
                (20, 49),
                (29, 49),
                (23, 63),
                (45, 43),
                (35, 43),
            ],
            fill=lightning_color,
            outline="black",
        )

        return image

    def create_tooltip(self):
        """Подсказка возле значка."""

        lines = [
            "Nord Pool Estonia",
            f"Сейчас: {self.price:.2f} c/kWh",
        ]

        if self.next_price is not None:
            lines.append(f"Следующие 15 мин: " f"{self.next_price:.2f} c/kWh")

        if self.tomorrow_count > 0:
            lines.append(f"Завтра опубликовано: " f"{self.tomorrow_count}/96")

        else:
            lines.append("Завтра: данных пока нет")

        return "\n".join(lines)

    # ==========================================================
    # PRICE UPDATE
    # ==========================================================

    def update_prices(self):
        """Обновляет текущую цену."""

        prices = elering.get_current_and_next_estonia_price()

        self.price = prices["current"]["cents_kwh"]

        if prices["next"] is not None:
            self.next_price = prices["next"]["cents_kwh"]

        else:
            self.next_price = None

        self.icon.icon = self.create_icon(self.price)

        self.icon.title = self.create_tooltip()

    def update_tomorrow_prices(self):
        """Проверяет публикацию цен завтра."""

        tomorrow = elering.get_tomorrow_hourly_prices()

        new_count = len(tomorrow)
        old_count = self.tomorrow_count

        self.tomorrow_count = new_count

        self.icon.title = self.create_tooltip()

        if new_count > old_count:

            try:
                self.icon.notify(
                    (
                        "Опубликованы новые "
                        "цены на завтра: "
                        f"{new_count}/96 интервалов"
                    ),
                    "Electricity Estonia",
                )

            except Exception:
                pass

    # ==========================================================
    # PANEL
    # ==========================================================

    def open_panel(self, icon, item):
        """
        Левый клик по значку.

        Если панели нет — создаём её.
        Если она уже существует —
        отправляем ей сигнал подняться.
        """

        with self.panel_lock:

            if self.panel_open:

                self.show_panel_event.set()
                return

            # ВАЖНО:
            # флаг ставим до запуска потока,
            # чтобы быстрый двойной клик
            # не создал два окна.
            self.panel_open = True

        panel_thread = threading.Thread(
            target=self.run_panel,
            daemon=True,
        )

        panel_thread.start()

    def run_panel(self):
        """Работает исключительно в потоке Tkinter."""

        try:

            panel = PricePanel(
                current_price=self.price,
                next_price=self.next_price,
            )

            self.panel = panel

            panel.root.protocol(
                "WM_DELETE_WINDOW",
                panel.root.destroy,
            )

            # Tkinter сам проверяет Event.
            # Никаких вызовов Tk из потока pystray.
            self.check_panel_activation()

            panel.run()

        finally:

            self.panel = None

            self.show_panel_event.clear()

            with self.panel_lock:
                self.panel_open = False

    def check_panel_activation(self):
        """
        Выполняется только Tk-потоком.

        Если tray запросил показ панели —
        окно поднимает само себя.
        """

        if self.panel is None:
            return

        root = self.panel.root

        try:

            if self.show_panel_event.is_set():

                self.show_panel_event.clear()

                root.deiconify()
                root.lift()

                # Короткий topmost гарантирует,
                # что окно окажется впереди.
                root.attributes(
                    "-topmost",
                    True,
                )

                root.after(
                    100,
                    lambda: root.attributes(
                        "-topmost",
                        False,
                    ),
                )

                root.focus_force()

            # Проверяем сигнал 5 раз/сек.
            root.after(
                200,
                self.check_panel_activation,
            )

        except Exception:
            pass

    # ==========================================================
    # MENU
    # ==========================================================

    def refresh(self, icon, item):
        """Ручное обновление."""

        try:

            self.update_prices()
            self.update_tomorrow_prices()

        except Exception as error:

            self.icon.title = f"Ошибка обновления: {error}"

    # ==========================================================
    # BACKGROUND LOOPS
    # ==========================================================

    def current_price_loop(self):
        """Обновляет текущую цену каждые 15 минут."""

        while self.running:

            now = datetime.now()

            minutes_until_next = 15 - (now.minute % 15)

            seconds_until_next = minutes_until_next * 60 - now.second + 5

            time.sleep(seconds_until_next)

            if not self.running:
                break

            try:
                self.update_prices()

            except Exception as error:

                self.icon.title = f"Ошибка цены: {error}"

    def tomorrow_price_loop(self):
        """Проверяет публикацию завтрашних цен."""

        while self.running:

            time.sleep(15 * 60)

            if not self.running:
                break

            today = datetime.now().date()

            if today != self.tomorrow_monitor_date:

                self.tomorrow_monitor_date = today
                self.tomorrow_count = 0

                self.icon.title = self.create_tooltip()

            if self.tomorrow_count >= 96:
                continue

            try:
                self.update_tomorrow_prices()

            except Exception:
                pass

    # ==========================================================
    # EXIT
    # ==========================================================

    def exit_program(self, icon, item):
        """Завершает приложение."""

        self.running = False

        # Если панель существует,
        # просим её закрыться в её собственном потоке.
        if self.panel is not None:

            try:
                self.panel.root.after(
                    0,
                    self.panel.root.destroy,
                )

            except Exception:
                pass

        icon.stop()

    def run(self):
        """Запускает фоновые потоки и tray."""

        current_thread = threading.Thread(
            target=self.current_price_loop,
            daemon=True,
        )

        tomorrow_thread = threading.Thread(
            target=self.tomorrow_price_loop,
            daemon=True,
        )

        current_thread.start()
        tomorrow_thread.start()

        self.icon.run()
