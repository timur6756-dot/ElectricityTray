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

        self.icon = pystray.Icon(
            "ElectricityTray",
            self.create_icon(self.price),
            self.create_tooltip(),
            menu=pystray.Menu(
                pystray.MenuItem("Открыть панель", self.open_panel),
                pystray.MenuItem("Обновить", self.refresh),
                pystray.MenuItem("Выход", self.exit_program),
            ),
        )

        self.running = True

    def get_price_color(self, price):
        """Возвращает цвет молнии в зависимости от цены."""

        if price < config.PRICE_CHEAP:
            return "green"

        if price < config.PRICE_NORMAL:
            return "gold"

        if price < config.PRICE_EXPENSIVE:
            return "orange"

        return "red"

    def create_icon(self, price):
        """Создаёт иконку: цена сверху, молния снизу."""

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

        lightning_color = self.get_price_color(
            price
        )

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
        """Создаёт подсказку при наведении."""

        if self.next_price is not None:
            return (
                f"Nord Pool Estonia\n"
                f"Сейчас: {self.price:.2f} c/kWh\n"
                f"Следующие 15 мин: "
                f"{self.next_price:.2f} c/kWh"
            )

        return (
            f"Nord Pool Estonia\n"
            f"Сейчас: {self.price:.2f} c/kWh\n"
            f"Следующая цена недоступна"
        )

    def update_prices(self):
        """Получает свежие цены."""

        prices = (
            elering.get_current_and_next_estonia_price()
        )

        self.price = (
            prices["current"]["cents_kwh"]
        )

        if prices["next"] is not None:
            self.next_price = (
                prices["next"]["cents_kwh"]
            )
        else:
            self.next_price = None

        self.icon.icon = self.create_icon(
            self.price
        )

        self.icon.title = self.create_tooltip()

    def open_panel(self, icon, item):
        """Открывает информационную панель."""

        panel_thread = threading.Thread(
            target=self.run_panel,
            daemon=True,
        )

        panel_thread.start()

    def run_panel(self):
        """Запускает окно панели."""

        panel = PricePanel(
            current_price=self.price,
            next_price=self.next_price,
        )

        panel.run()

    def refresh(self, icon, item):
        """Обновляет цену вручную."""

        try:
            self.update_prices()

        except Exception as error:
            self.icon.title = (
                f"Ошибка обновления: {error}"
            )

    def auto_update_loop(self):
        """
        Автоматически обновляет цену
        на границах 15-минутных интервалов.
        """

        while self.running:

            now = datetime.now()

            minutes_until_next = (
                15 - (now.minute % 15)
            )

            seconds_until_next = (
                minutes_until_next * 60
                - now.second
            )

            seconds_until_next += 5

            time.sleep(
                seconds_until_next
            )

            if not self.running:
                break

            try:
                self.update_prices()

            except Exception as error:
                self.icon.title = (
                    f"Ошибка обновления: {error}"
                )

    def exit_program(self, icon, item):
        """Завершает программу."""

        self.running = False
        icon.stop()

    def run(self):
        """Запускает обновление и tray."""

        update_thread = threading.Thread(
            target=self.auto_update_loop,
            daemon=True,
        )

        update_thread.start()

        self.icon.run()