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
    """Возвращает текущую цену электроэнергии в Эстонии."""

    data = get_prices()
    prices = data["data"]["ee"]

    now = int(time.time())

    current = None

    for item in prices:
        if item["timestamp"] <= now:
            current = item
        else:
            break

    if current is None:
        raise RuntimeError("Current Estonia price not found")

    eur_mwh = current["price"]
    cents_kwh = eur_mwh / 10

    return {
        "timestamp": current["timestamp"],
        "eur_mwh": eur_mwh,
        "cents_kwh": cents_kwh,
    }


def get_current_and_next_estonia_price():
    """Возвращает текущую и следующую 15-минутную цену в Эстонии."""

    data = get_prices()
    prices = data["data"]["ee"]

    now = int(time.time())

    current = None
    next_price = None

    for index, item in enumerate(prices):
        if item["timestamp"] <= now:
            current = item

            if index + 1 < len(prices):
                next_price = prices[index + 1]
        else:
            break

    if current is None:
        raise RuntimeError("Current Estonia price not found")

    result = {
        "current": {
            "timestamp": current["timestamp"],
            "eur_mwh": current["price"],
            "cents_kwh": current["price"] / 10,
        },
        "next": None,
    }

    if next_price is not None:
        result["next"] = {
            "timestamp": next_price["timestamp"],
            "eur_mwh": next_price["price"],
            "cents_kwh": next_price["price"] / 10,
        }

    return result


if __name__ == "__main__":
    prices = get_current_and_next_estonia_price()

    print("Estonia electricity prices")

    print(
        f"Current : "
        f"{prices['current']['eur_mwh']:.2f} EUR/MWh"
        f" = {prices['current']['cents_kwh']:.2f} c/kWh"
    )

    if prices["next"] is not None:
        print(
            f"Next    : "
            f"{prices['next']['eur_mwh']:.2f} EUR/MWh"
            f" = {prices['next']['cents_kwh']:.2f} c/kWh"
        )
    else:
        print("Next    : not available")