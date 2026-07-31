from PIL import Image, ImageDraw, ImageFont
import pystray
import threading
import time
from datetime import datetime

import config
import elering

from i18n import (
    LANGUAGE_NAMES,
    normalize_language,
    t,
)

from panel import PricePanel

from settings import (
    load_settings,
    save_language,
)


class TrayIcon:

    def __init__(self):

        # ---------------------------------
        # Language
        # ---------------------------------

        settings = load_settings()

        self.language = normalize_language(
            settings.get(
                "language",
                "ru",
            )
        )

        # ---------------------------------
        # Price
        # ---------------------------------

        prices = elering.get_current_and_next_estonia_price()

        self.price = prices["current"]["cents_kwh"]

        if prices["next"] is not None:

            self.next_price = prices["next"]["cents_kwh"]

        else:

            self.next_price = None

        # ---------------------------------
        # Tomorrow
        # ---------------------------------

        self.tomorrow_count = 0

        self.tomorrow_monitor_date = datetime.now().date()

        try:

            tomorrow = elering.get_tomorrow_hourly_prices()

            self.tomorrow_count = len(tomorrow)

        except Exception:

            self.tomorrow_count = 0

        # ---------------------------------
        # Panel single instance
        # ---------------------------------

        self.panel = None
        self.panel_open = False

        self.panel_lock = threading.Lock()

        self.show_panel_event = threading.Event()

        self.close_panel_event = threading.Event()

        # ---------------------------------
        # Tray
        # ---------------------------------

        self.icon = pystray.Icon(
            "ElectricityTray",
            self.create_icon(self.price),
            self.create_tooltip(),
            menu=self.create_menu(),
        )

        self.running = True

    # ======================================================
    # LANGUAGE
    # ======================================================

    def get_language(self):
        return self.language

    def set_language(
        self,
        language,
    ):
        """Меняет язык всего приложения."""

        language = normalize_language(language)

        self.language = language

        save_language(language)

        self.icon.title = self.create_tooltip()

        # Перестраиваем tray menu.
        self.icon.menu = self.create_menu()

        try:
            self.icon.update_menu()

        except Exception:
            pass

    def create_menu(self):
        """Создаёт локализованное меню tray."""

        language_menu = pystray.Menu(
            pystray.MenuItem(
                LANGUAGE_NAMES["ru"],
                lambda icon, item: self.set_language("ru"),
                checked=lambda item: self.language == "ru",
                radio=True,
            ),
            pystray.MenuItem(
                LANGUAGE_NAMES["en"],
                lambda icon, item: self.set_language("en"),
                checked=lambda item: self.language == "en",
                radio=True,
            ),
            pystray.MenuItem(
                LANGUAGE_NAMES["et"],
                lambda icon, item: self.set_language("et"),
                checked=lambda item: self.language == "et",
                radio=True,
            ),
        )

        return pystray.Menu(
            pystray.MenuItem(
                t(
                    "open_panel",
                    self.language,
                ),
                self.open_panel,
                default=True,
            ),
            pystray.MenuItem(
                t(
                    "refresh",
                    self.language,
                ),
                self.refresh,
            ),
            pystray.MenuItem(
                t(
                    "language",
                    self.language,
                ),
                language_menu,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                t(
                    "exit",
                    self.language,
                ),
                self.exit_program,
            ),
        )

    # ======================================================
    # ICON
    # ======================================================

    def get_price_color(
        self,
        price,
    ):

        if price < config.PRICE_CHEAP:
            return "green"

        if price < config.PRICE_NORMAL:
            return "gold"

        if price < config.PRICE_EXPENSIVE:
            return "orange"

        return "red"

    def create_icon(
        self,
        price,
    ):

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

        lines = [
            "Nord Pool Estonia",
            t(
                "tray_now",
                self.language,
                price=self.price,
            ),
        ]

        if self.next_price is not None:

            lines.append(
                t(
                    "tray_next",
                    self.language,
                    price=self.next_price,
                )
            )

        if self.tomorrow_count > 0:

            lines.append(
                t(
                    "tray_tomorrow",
                    self.language,
                    count=self.tomorrow_count,
                )
            )

        else:

            lines.append(
                t(
                    "tray_tomorrow_none",
                    self.language,
                )
            )

        return "\n".join(lines)

    # ======================================================
    # PRICE
    # ======================================================

    def update_prices(self):

        prices = elering.get_current_and_next_estonia_price()

        self.price = prices["current"]["cents_kwh"]

        if prices["next"] is not None:

            self.next_price = prices["next"]["cents_kwh"]

        else:

            self.next_price = None

        self.icon.icon = self.create_icon(self.price)

        self.icon.title = self.create_tooltip()

    def update_tomorrow_prices(self):

        tomorrow = elering.get_tomorrow_hourly_prices()

        new_count = len(tomorrow)

        old_count = self.tomorrow_count

        self.tomorrow_count = new_count

        self.icon.title = self.create_tooltip()

        if new_count > old_count:

            try:

                self.icon.notify(
                    t(
                        "new_prices",
                        self.language,
                        count=new_count,
                    ),
                    t(
                        "new_prices_title",
                        self.language,
                    ),
                )

            except Exception:

                pass

    # ======================================================
    # PANEL
    # ======================================================

    def open_panel(
        self,
        icon,
        item,
    ):

        with self.panel_lock:

            if self.panel_open:

                self.show_panel_event.set()

                return

            self.panel_open = True

        panel_thread = threading.Thread(
            target=self.run_panel,
            daemon=True,
        )

        panel_thread.start()

    def run_panel(self):

        try:

            panel = PricePanel(
                current_price=self.price,
                next_price=self.next_price,
                language=self.language,
                language_getter=(self.get_language),
                language_setter=(self.set_language),
            )

            self.panel = panel

            panel.root.protocol(
                "WM_DELETE_WINDOW",
                panel.root.destroy,
            )

            self.check_panel_events()

            panel.run()

        finally:

            self.panel = None

            self.show_panel_event.clear()
            self.close_panel_event.clear()

            with self.panel_lock:

                self.panel_open = False

    def check_panel_events(self):

        if self.panel is None:
            return

        root = self.panel.root

        try:

            if self.close_panel_event.is_set():

                self.close_panel_event.clear()

                root.destroy()

                return

            if self.show_panel_event.is_set():

                self.show_panel_event.clear()

                root.deiconify()
                root.lift()

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

            root.after(
                200,
                self.check_panel_events,
            )

        except Exception:

            pass

    # ======================================================
    # REFRESH
    # ======================================================

    def refresh(
        self,
        icon,
        item,
    ):

        try:

            self.update_prices()

            self.update_tomorrow_prices()

        except Exception as error:

            self.icon.title = t(
                "update_error",
                self.language,
                error=error,
            )

    # ======================================================
    # BACKGROUND
    # ======================================================

    def current_price_loop(self):

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

                self.icon.title = t(
                    "price_error",
                    self.language,
                    error=error,
                )

    def tomorrow_price_loop(self):

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

    # ======================================================
    # EXIT
    # ======================================================

    def exit_program(
        self,
        icon,
        item,
    ):

        self.running = False

        if self.panel_open:

            self.close_panel_event.set()

        icon.stop()

    def run(self):

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
