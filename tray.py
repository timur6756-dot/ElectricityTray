import threading
from datetime import datetime

import pystray
from PIL import Image, ImageDraw, ImageFont

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

    # Как часто проверяем системное время и состояние обновления.
    TIME_CHECK_SECONDS = 30

    # Если между проверками прошло больше этого времени,
    # считаем, что Windows выходила из сна или гибернации.
    SLEEP_DETECTION_SECONDS = 90

    # Как часто проверяем цены следующего дня.
    TOMORROW_CHECK_SECONDS = 15 * 60

    # Windows ограничивает длину tooltip tray.
    MAX_TRAY_TITLE_LENGTH = 127

    def __init__(self):

        # ==================================================
        # LANGUAGE
        # ==================================================

        user_settings = load_settings()

        self.language = normalize_language(
            user_settings.get(
                "language",
                "ru",
            )
        )

        # ==================================================
        # APPLICATION STATE
        # ==================================================

        self.running = True

        # Общий сигнал остановки фоновых потоков.
        self.stop_event = threading.Event()

        # ==================================================
        # CURRENT PRICE
        # ==================================================

        prices = elering.get_current_and_next_estonia_price()

        self.price = prices["current"]["cents_kwh"]

        if prices["next"] is not None:

            self.next_price = prices["next"]["cents_kwh"]

        else:

            self.next_price = None

        # ==================================================
        # TOMORROW
        # ==================================================

        self.tomorrow_count = 0

        self.tomorrow_monitor_date = datetime.now().date()

        try:

            tomorrow = elering.get_tomorrow_hourly_prices()

            self.tomorrow_count = len(tomorrow)

        except Exception:

            self.tomorrow_count = 0

        # ==================================================
        # SINGLE PANEL
        # ==================================================

        self.panel = None
        self.panel_open = False

        self.panel_lock = threading.Lock()

        # Сигнал существующей панели:
        # выйти на передний план.
        self.show_panel_event = threading.Event()

        # Сигнал закрыть панель из её Tk-потока.
        self.close_panel_event = threading.Event()

        # ==================================================
        # TRAY ICON
        # ==================================================

        self.icon = pystray.Icon(
            "ElectricityTray",
            self.create_icon(self.price),
            self.create_tooltip(),
            menu=self.create_menu(),
        )

    # ======================================================
    # SAFE TRAY TITLE
    # ======================================================

    def set_tray_title(
        self,
        text,
    ):
        """
        Безопасно устанавливает tooltip tray.

        Windows ограничивает длину строки.
        Длинное исключение не должно завершать
        фоновый поток обновления.
        """

        safe_text = (
            str(text)
            .replace(
                "\r",
                " ",
            )
            .replace(
                "\n",
                " ",
            )
        )

        safe_text = safe_text[: self.MAX_TRAY_TITLE_LENGTH]

        try:

            self.icon.title = safe_text

        except Exception:

            # Ошибка tooltip не должна
            # останавливать приложение.
            pass

    def set_update_error_title(self):
        """
        Показывает короткое сообщение
        о временной недоступности Elering.
        """

        messages = {
            "ru": ("Нет соединения с Elering. " "Повтор через 30 секунд."),
            "en": ("Cannot connect to Elering. " "Retrying in 30 seconds."),
            "et": ("Eleringiga ei saa ühendust. " "Uus katse 30 sekundi pärast."),
        }

        self.set_tray_title(
            messages.get(
                self.language,
                messages["ru"],
            )
        )

    # ======================================================
    # LANGUAGE
    # ======================================================

    def get_language(self):
        """Возвращает текущий язык."""

        return self.language

    def set_language(
        self,
        language,
    ):
        """Меняет язык интерфейса."""

        language = normalize_language(language)

        self.language = language

        save_language(language)

        self.set_tray_title(self.create_tooltip())

        # Пересоздаём локализованное меню tray.
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
    # TRAY ICON IMAGE
    # ======================================================

    def get_price_color(
        self,
        price,
    ):
        """Определяет цвет молнии по цене."""

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
        """Создаёт изображение tray-значка."""

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
        """Создаёт локализованную подсказку tray."""

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
    # PRICE UPDATE
    # ======================================================

    def update_prices(self):
        """Получает текущую и следующую цену."""

        prices = elering.get_current_and_next_estonia_price()

        self.price = prices["current"]["cents_kwh"]

        if prices["next"] is not None:

            self.next_price = prices["next"]["cents_kwh"]

        else:

            self.next_price = None

        self.icon.icon = self.create_icon(self.price)

        self.set_tray_title(self.create_tooltip())

    def update_tomorrow_prices(self):
        """Получает доступные цены следующего дня."""

        tomorrow = elering.get_tomorrow_hourly_prices()

        new_count = len(tomorrow)

        old_count = self.tomorrow_count

        self.tomorrow_count = new_count

        self.set_tray_title(self.create_tooltip())

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
        """
        Открывает панель.

        Если панель уже существует,
        отправляет ей сигнал выйти вперёд.
        """

        with self.panel_lock:

            if self.panel_open:

                self.show_panel_event.set()

                return

            # Ставим флаг до запуска потока,
            # чтобы быстрый двойной клик
            # не создал два окна.
            self.panel_open = True

        panel_thread = threading.Thread(
            target=self.run_panel,
            daemon=True,
            name="ElectricityTrayPanel",
        )

        panel_thread.start()

    def run_panel(self):
        """Создаёт и запускает единственную панель."""

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
        """
        Проверяет сигналы tray
        внутри Tk-потока.
        """

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
    # MANUAL REFRESH
    # ======================================================

    def refresh(
        self,
        icon,
        item,
    ):
        """Ручное обновление из меню tray."""

        try:

            self.update_prices()
            self.update_tomorrow_prices()

        except Exception:

            self.set_update_error_title()

    # ======================================================
    # TIME HELPERS
    # ======================================================

    @staticmethod
    def get_interval_key(
        moment,
    ):
        """
        Возвращает уникальный ключ
        текущего 15-минутного интервала.
        """

        return (
            moment.year,
            moment.month,
            moment.day,
            moment.hour,
            moment.minute // 15,
        )

    # ======================================================
    # CURRENT PRICE BACKGROUND LOOP
    # ======================================================

    def current_price_loop(self):
        """
        Контролирует текущую цену.

        После сна Windows сеть может быть
        временно недоступна. В этом случае
        запрос повторяется через 30 секунд.
        """

        last_check = datetime.now()

        # None заставляет выполнить
        # обновление сразу после запуска.
        last_interval = None

        while self.running:

            now = datetime.now()

            current_interval = self.get_interval_key(now)

            elapsed_seconds = (now - last_check).total_seconds()

            resumed_from_sleep = elapsed_seconds > self.SLEEP_DETECTION_SECONDS

            interval_changed = current_interval != last_interval

            should_update = (
                last_interval is None or interval_changed or resumed_from_sleep
            )

            if should_update:

                try:

                    self.update_prices()

                    # Интервал запоминаем только
                    # после успешного запроса.
                    last_interval = current_interval

                except Exception:

                    self.set_update_error_title()

                    # last_interval не изменяем.
                    # Через 30 секунд условие
                    # снова вызовет update_prices().

            last_check = now

            if self.stop_event.wait(self.TIME_CHECK_SECONDS):

                break

    # ======================================================
    # TOMORROW BACKGROUND LOOP
    # ======================================================

    def tomorrow_price_loop(self):
        """
        Проверяет цены следующего дня.

        После ошибки сети запрос также
        повторяется, а поток не завершается.
        """

        last_check = datetime.now()

        # Первая проверка выполняется сразу.
        last_tomorrow_check = None

        while self.running:

            now = datetime.now()

            elapsed_since_loop_check = (now - last_check).total_seconds()

            resumed_from_sleep = elapsed_since_loop_check > self.SLEEP_DETECTION_SECONDS

            today = now.date()

            if today != self.tomorrow_monitor_date:

                self.tomorrow_monitor_date = today

                self.tomorrow_count = 0

                self.set_tray_title(self.create_tooltip())

                last_tomorrow_check = None

            if last_tomorrow_check is None:

                check_due = True

            else:

                seconds_since_tomorrow_check = (
                    now - last_tomorrow_check
                ).total_seconds()

                check_due = seconds_since_tomorrow_check >= self.TOMORROW_CHECK_SECONDS

            should_check = check_due or resumed_from_sleep

            if should_check and self.tomorrow_count < 96:

                try:

                    self.update_tomorrow_prices()

                    # Время проверки фиксируем
                    # только после успешного запроса.
                    last_tomorrow_check = now

                except Exception:

                    self.set_update_error_title()

                    # Оставляем прежнее время,
                    # чтобы через 30 секунд
                    # запрос повторился.

            last_check = now

            if self.stop_event.wait(self.TIME_CHECK_SECONDS):

                break

    # ======================================================
    # EXIT
    # ======================================================

    def exit_program(
        self,
        icon,
        item,
    ):
        """Полностью завершает приложение."""

        self.running = False

        self.stop_event.set()

        if self.panel_open:

            self.close_panel_event.set()

        icon.stop()

    # ======================================================
    # START
    # ======================================================

    def run(self):
        """Запускает фоновые потоки и tray."""

        current_thread = threading.Thread(
            target=self.current_price_loop,
            daemon=True,
            name="ElectricityTrayCurrentPrice",
        )

        tomorrow_thread = threading.Thread(
            target=self.tomorrow_price_loop,
            daemon=True,
            name="ElectricityTrayTomorrowPrice",
        )

        current_thread.start()
        tomorrow_thread.start()

        self.icon.run()
