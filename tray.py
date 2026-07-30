from PIL import Image, ImageDraw, ImageFont
import pystray
import threading
import time
from datetime import datetime

import elering
import config


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
            "white"
        )

        draw = ImageDraw.Draw(image)

        # Используем стандартный жирный Arial Windows
        try:
            font = ImageFont.truetype(
                "arialbd.ttf",
                34
            )

        except OSError:
            font = ImageFont.load_default()

        # Цена с одним знаком после запятой
        price_text = f"{price:.1f}"

        # Центрируем цену
        bbox = draw.textbbox(
            (0, 0),
            price_text,
            font=font
        )

        text_width = bbox[2] - bbox[0]

        x = (64 - text_width) // 2

        draw.text(
            (x, -5),
            price_text,
            font=font,
            fill="black",
        )

        # Определяем цвет молнии
        lightning_color = self.get_price_color(
            price
        )

        # Молния в нижней части иконки
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
        """Создаёт подсказку при наведении мыши."""

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
        """Получает свежие цены и обновляет иконку."""

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

        # Перерисовываем иконку
        self.icon.icon = self.create_icon(
            self.price
        )

        # Обновляем текст подсказки
        self.icon.title = self.create_tooltip()

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

            # Небольшая задержка после начала
            # нового рыночного интервала
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
        """Запускает автоматическое обновление и tray."""

        update_thread = threading.Thread(
            target=self.auto_update_loop,
            daemon=True,
        )

        update_thread.start()

        self.icon.run()