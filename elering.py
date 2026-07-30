import time
import requests


API_URL = "https://dashboard.elering.ee/api/nps/price"


def get_prices():
    """Получает биржевые цены от Elering."""
    response = requests.get(API_URL, timeout=10)
    response.raise_for_status()

    data = response.json()

    if not data.get("success"):
        raise RuntimeError("Elering API returned success=False")

    return data


def get_current_estonia_price():
    """Возвращает текущую биржевую цену электроэнергии в Эстонии."""

    data = get_prices()
    prices = data["data"]["ee"]

    now = int(time.time())

    # Ищем последний опубликованный интервал,
    # timestamp которого не превышает текущее время.
    current = None

    for item in prices:
        if item["timestamp"] <= now:
            current = item
        else:
            break

    if current is None:
        raise RuntimeError("Current Estonia price not found")

    eur_mwh = current["price"]

    # 1 €/MWh = 0.1 c/kWh
    cents_kwh = eur_mwh / 10

    return {
        "timestamp": current["timestamp"],
        "eur_mwh": eur_mwh,
        "cents_kwh": cents_kwh,
    }


if __name__ == "__main__":
    price = get_current_estonia_price()

    print("Estonia electricity price")
    print(f"EUR/MWh : {price['eur_mwh']:.2f}")
    print(f"c/kWh   : {price['cents_kwh']:.2f}")