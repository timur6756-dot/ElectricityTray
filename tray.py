from PIL import Image, ImageDraw
import pystray


class TrayIcon:

    def __init__(self):
        self.icon = pystray.Icon(
            "ElectricityTray",
            self.create_icon(),
            "Electricity Monitor",
            menu=pystray.Menu(
                pystray.MenuItem("Выход", self.exit_program)
            )
        )

    def create_icon(self):
        image = Image.new("RGB", (64, 64), "white")
        draw = ImageDraw.Draw(image)

        draw.polygon(
            [
                (30, 5),
                (18, 32),
                (30, 32),
                (20, 58),
                (46, 24),
                (34, 24),
            ],
            fill="gold",
            outline="black",
        )

        return image

    def exit_program(self, icon, item):
        icon.stop()

    def run(self):
        self.icon.run()