from PIL import Image, ImageDraw, ImageFont
import pystray

from elering import get_current_estonia_price


class TrayIcon:

    def __init__(self):
        price = get_current_estonia_price()
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
            price = get_current_estonia_price()
            self.price = price["cents_kwh"]

            self.icon.icon = self.create_icon(self.price)
            self.icon.title = self.create_tooltip()

        except Exception as error:
            self.icon.title = f"Ошибка обновления: {error}"

    def exit_program(self, icon, item):
        icon.stop()

    def run(self):
        self.icon.run()