import tkinter as tk
from datetime import datetime


class PricePanel:

    def __init__(self, current_price, next_price):
        self.current_price = current_price
        self.next_price = next_price

        self.root = tk.Tk()

        self.root.title("Electricity Estonia")
        self.root.geometry("320x220")
        self.root.resizable(False, False)

        # Основной заголовок
        title = tk.Label(
            self.root,
            text="ELECTRICITY · ESTONIA",
            font=("Arial", 12, "bold"),
        )
        title.pack(pady=(15, 5))

        # Текущая цена
        current = tk.Label(
            self.root,
            text=f"{self.current_price:.2f} c/kWh",
            font=("Arial", 28, "bold"),
        )
        current.pack(pady=(5, 0))

        current_label = tk.Label(
            self.root,
            text="сейчас",
            font=("Arial", 10),
        )
        current_label.pack()

        # Текущий интервал времени
        now = datetime.now()

        interval_minute = (now.minute // 15) * 15

        interval_text = f"{now.hour:02d}:{interval_minute:02d}"

        time_label = tk.Label(
            self.root,
            text=f"Текущий интервал: {interval_text}",
            font=("Arial", 10),
        )
        time_label.pack(pady=(12, 5))

        # Следующая цена
        if self.next_price is not None:
            next_text = f"Следующие 15 мин: " f"{self.next_price:.2f} c/kWh"
        else:
            next_text = "Следующая цена недоступна"

        next_label = tk.Label(
            self.root,
            text=next_text,
            font=("Arial", 11),
        )
        next_label.pack(pady=5)

        # Кнопка закрытия
        close_button = tk.Button(
            self.root,
            text="Закрыть",
            command=self.root.destroy,
            width=12,
        )
        close_button.pack(pady=15)

    def run(self):
        self.root.mainloop()

