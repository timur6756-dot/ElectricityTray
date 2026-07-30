from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

API_URL = "https://estfeed.elering.ee/" "api/public/v1/energy-price/electricity"

ESTONIA_TZ = ZoneInfo("Europe/Tallinn")


def to_utc_string(dt, milliseconds="000"):
    """Преобразует datetime в UTC-строку для API Estfeed."""

    utc_dt = dt.astimezone(timezone.utc)

    return utc_dt.strftime(f"%Y-%m-%dT%H:%M:%S.{milliseconds}Z")


def get_day_range(target_date):
    """Возвращает UTC-границы календарного дня в Эстонии."""

    start_local = datetime(
        target_date.year,
        target_date.month,
        target_date.day,
        0,
        0,
        0,
        tzinfo=ESTONIA_TZ,
    )

    end_local = start_local + timedelta(days=1) - timedelta(milliseconds=1)

    return (
        to_utc_string(start_local, "000"),
        to_utc_string(end_local, "999"),
    )


def get_raw_prices(
    start_datetime,
    end_datetime,
    resolution,
):
    """Выполняет запрос к Estfeed API."""

    params = {
        "startDateTime": to_utc_string(
            start_datetime,
            "000",
        ),
        "endDateTime": to_utc_string(
            end_datetime,
            "999",
        ),
        "resolution": resolution,
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def get_raw_day_prices(
    target_date,
    resolution="one_hour",
):
    """Получает цены выбранного календарного дня."""

    start, end = get_day_range(target_date)

    params = {
        "startDateTime": start,
        "endDateTime": end,
        "resolution": resolution,
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def normalize_day_prices(
    target_date,
    resolution="one_hour",
):
    """Преобразует ответ API в удобный список."""

    raw_data = get_raw_day_prices(
        target_date,
        resolution,
    )

    result = []

    for item in raw_data:
        from_time = datetime.fromisoformat(item["fromDateTime"])

        result.append(
            {
                "date": target_date,
                "time": from_time,
                "time_text": from_time.strftime("%H:%M"),
                "cents_kwh": item["centsPerKwh"],
                "cents_kwh_vat": item["centsPerKwhWithVat"],
                "eur_mwh": item["eurPerMwh"],
                "eur_mwh_vat": item["eurPerMwhWithVat"],
            }
        )

    return result


def get_current_and_next_estonia_price():
    """
    Возвращает настоящую текущую
    и следующую 15-минутную цену.
    """

    now = datetime.now(ESTONIA_TZ)

    # Берём диапазон вокруг текущего момента
    start = now - timedelta(minutes=30)
    end = now + timedelta(minutes=45)

    data = get_raw_prices(
        start,
        end,
        resolution="fifteen_minutes",
    )

    current_item = None
    next_item = None

    for index, item in enumerate(data):

        item_start = datetime.fromisoformat(item["fromDateTime"])

        item_end = datetime.fromisoformat(item["toDateTime"])

        if item_start <= now <= item_end:
            current_item = item

            if index + 1 < len(data):
                next_item = data[index + 1]

            break

    if current_item is None:
        raise RuntimeError("Current Estonia price not found")

    result = {
        "current": {
            "timestamp": current_item["fromDateTime"],
            "eur_mwh": current_item["eurPerMwh"],
            "cents_kwh": current_item["centsPerKwh"],
            "cents_kwh_vat": current_item["centsPerKwhWithVat"],
        },
        "next": None,
    }

    if next_item is not None:
        result["next"] = {
            "timestamp": next_item["fromDateTime"],
            "eur_mwh": next_item["eurPerMwh"],
            "cents_kwh": next_item["centsPerKwh"],
            "cents_kwh_vat": next_item["centsPerKwhWithVat"],
        }

    return result


def get_today_hourly_prices():
    """Почасовые цены сегодняшнего дня."""

    today = datetime.now(ESTONIA_TZ).date()

    return normalize_day_prices(
        today,
        resolution="one_hour",
    )


def get_tomorrow_hourly_prices():
    """Почасовые цены следующего дня."""

    tomorrow = datetime.now(ESTONIA_TZ).date() + timedelta(days=1)

    try:
        return normalize_day_prices(
            tomorrow,
            resolution="one_hour",
        )

    except requests.HTTPError:
        return []


def get_day_stats(prices):
    """Статистика по суточному списку цен."""

    if not prices:
        return None

    values = [item["cents_kwh"] for item in prices]

    min_item = min(
        prices,
        key=lambda item: item["cents_kwh"],
    )

    max_item = max(
        prices,
        key=lambda item: item["cents_kwh"],
    )

    return {
        "minimum": min(values),
        "minimum_time": min_item["time_text"],
        "maximum": max(values),
        "maximum_time": max_item["time_text"],
        "average": sum(values) / len(values),
        "intervals": len(prices),
    }


if __name__ == "__main__":

    print()
    print("CURRENT 15-MINUTE PRICES")
    print("------------------------------------")

    prices = get_current_and_next_estonia_price()

    print(
        "Current:",
        f"{prices['current']['cents_kwh']:.3f}",
        "c/kWh",
    )

    if prices["next"]:
        print(
            "Next:",
            f"{prices['next']['cents_kwh']:.3f}",
            "c/kWh",
        )

    print()
    print("TODAY HOURLY")
    print("------------------------------------")

    today = get_today_hourly_prices()

    stats = get_day_stats(today)

    print("Intervals:", stats["intervals"])
    print(
        "Minimum:",
        f"{stats['minimum']:.2f}",
        "at",
        stats["minimum_time"],
    )
    print(
        "Maximum:",
        f"{stats['maximum']:.2f}",
        "at",
        stats["maximum_time"],
    )
    print(
        "Average:",
        f"{stats['average']:.2f}",
    )
