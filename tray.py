from PIL import Image, ImageDraw, ImageFont
import pystray
import threading
import time
from datetime import datetime

import elering


class TrayIcon:

    def __init__(self):
        price = elering.get_current_estonia_price()
        self.price = price["cents_kwh"]

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

    def create_icon(self, price):
        """Создаёт иконку: цена сверху, молния снизу."""

        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)

        # Используем стандартный шрифт Windows
        try:
            font = ImageFont.truetype("arialbd.ttf", 34)
        except OSError:
            font = ImageFont.load_default()

        # Цена с одним знаком после запятой
        price_text = f"{price:.1f}"

        # Центрируем текст
        bbox = draw.textbbox((0, 0), price_text, font=font)
        text_width = bbox[2] - bbox[0]

        x = (64 - text_width) // 2

        draw.text(
            (x, -5),
            price_text,
            font=font,
            fill="black",
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
            fill="gold",
            outline="black",
        )

        return image

    def create_tooltip(self):
        return f"Nord Pool Estonia: {self.price:.2f} c/kWh"

    def refresh(self, icon, item):
        """Обновляет цену вручную."""

        try:
            price = elering.get_current_estonia_price()
            self.price = price["cents_kwh"]

            self.icon.icon = self.create_icon(self.price)
            self.icon.title = self.create_tooltip()

        except Exception as error:
            self.icon.title = f"Ошибка обновления: {error}"


    def auto_update_loop(self):
        """Автоматически обновляет цену каждые 15 минут."""

        while self.running:
            now = datetime.now()

            minutes_until_next = 15 - (now.minute % 15)

            seconds_until_next = (
                minutes_until_next * 60
                - now.second
            )

            # Ждём ещё 5 секунд после начала нового интервала
            seconds_until_next += 5

            time.sleep(seconds_until_next)

            if not self.running:
                break

            try:
                price = elering.get_current_estonia_price()
                self.price = price["cents_kwh"]

                self.icon.icon = self.create_icon(self.price)
                self.icon.title = self.create_tooltip()

            except Exception as error:
                self.icon.title = f"Ошибка обновления: {error}"

    def exit_program(self, icon, item):
        self.running = False
        icon.stop()

    def run(self):
        update_thread = threading.Thread(
            target=self.auto_update_loop,
            daemon=True,
        )

        update_thread.start()
        self.icon.run()