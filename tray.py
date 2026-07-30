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

        # Сколько данных на завтра
        # было известно при последней проверке.
        self.tomorrow_count = 0

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

    def get_price_color(
        self,
        price,
    ):
        """Цвет молнии по текущей цене."""

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
        """Цена сверху, молния снизу."""

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
        """Подсказка tray."""

        lines = [
            "Nord Pool Estonia",
            (f"Сейчас: " f"{self.price:.2f} c/kWh"),
        ]

        if self.next_price is not None:
            lines.append("Следующие 15 мин: " f"{self.next_price:.2f} " "c/kWh")

        if self.tomorrow_count > 0:
            lines.append("Завтра опубликовано: " f"{self.tomorrow_count}/24 ч")
        else:
            lines.append("Завтра: данных пока нет")

        return "\n".join(lines)

    def update_prices(self):
        """Обновляет текущие 15-минутные цены."""

        prices = elering.get_current_and_next_estonia_price()

        self.price = prices["current"]["cents_kwh"]

        if prices["next"] is not None:
            self.next_price = prices["next"]["cents_kwh"]
        else:
            self.next_price = None

        self.icon.icon = self.create_icon(self.price)

        self.icon.title = self.create_tooltip()

    def update_tomorrow_prices(self):
        """Проверяет появление новых данных на завтра."""

        tomorrow = elering.get_tomorrow_hourly_prices()

        new_count = len(tomorrow)

        old_count = self.tomorrow_count

        self.tomorrow_count = new_count

        self.icon.title = self.create_tooltip()

        # Windows notification от pystray
        # используем только если реально
        # появились новые значения.
        if new_count > old_count:

            try:
                self.icon.notify(
                    ("Опубликованы новые " "цены на завтра: " f"{new_count}/24 часов"),
                    "Electricity Estonia",
                )

            except Exception:
                pass

    def open_panel(
        self,
        icon,
        item,
    ):
        """Открывает информационную панель."""

        panel_thread = threading.Thread(
            target=self.run_panel,
            daemon=True,
        )

        panel_thread.start()

    def run_panel(self):
        """Запускает PricePanel."""

        panel = PricePanel(
            current_price=self.price,
            next_price=self.next_price,
        )

        panel.run()

    def refresh(
        self,
        icon,
        item,
    ):
        """Ручное обновление всего."""

        try:
            self.update_prices()
            self.update_tomorrow_prices()

        except Exception as error:
            self.icon.title = f"Ошибка обновления: " f"{error}"

    def current_price_loop(self):
        """
        Текущая цена обновляется
        на границах 15-минутных интервалов.
        """

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
                self.icon.title = f"Ошибка цены: " f"{error}"

    def tomorrow_price_loop(self):
        """
        Фоновая проверка завтрашних цен
        каждые 15 минут.
        """

        while self.running:

            # 15 минут
            time.sleep(15 * 60)

            if not self.running:
                break

            try:
                self.update_tomorrow_prices()

            except Exception:
                # Ошибка сети не должна
                # останавливать приложение.
                pass

    def exit_program(
        self,
        icon,
        item,
    ):
        """Завершает приложение."""

        self.running = False
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
