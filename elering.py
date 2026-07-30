from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

API_URL = "https://estfeed.elering.ee/" "api/public/v1/energy-price/electricity"

ESTONIA_TZ = ZoneInfo("Europe/Tallinn")


def to_utc_string(dt, milliseconds="000"):
    """
    Преобразует datetime в UTC-строку,
    подходящую для API Estfeed.
    """

    utc_dt = dt.astimezone(timezone.utc)

    return utc_dt.strftime(f"%Y-%m-%dT%H:%M:%S.{milliseconds}Z")


def get_day_range(target_date):
    """
    Возвращает UTC-границы календарного дня
    в часовом поясе Эстонии.
    """

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

    start_utc = to_utc_string(
        start_local,
        milliseconds="000",
    )

    end_utc = to_utc_string(
        end_local,
        milliseconds="999",
    )

    return start_utc, end_utc


def get_raw_day_prices(
    target_date,
    resolution="one_hour",
):
    """
    Получает сырой ответ Estfeed
    для выбранного дня.
    """

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
    """
    Преобразует сырой ответ API
    в удобный список цен.
    """

    raw_data = get_raw_day_prices(
        target_date,
        resolution=resolution,
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


def get_today_hourly_prices():
    """
    Возвращает почасовые цены
    сегодняшнего дня.
    """

    today = datetime.now(ESTONIA_TZ).date()

    return normalize_day_prices(
        today,
        resolution="one_hour",
    )


def get_tomorrow_hourly_prices():
    """
    Возвращает почасовые цены
    следующего дня.

    Если цены ещё не опубликованы,
    возвращает пустой список.
    """

    tomorrow = datetime.now(ESTONIA_TZ).date() + timedelta(days=1)

    try:
        return normalize_day_prices(
            tomorrow,
            resolution="one_hour",
        )

    except requests.HTTPError:
        return []


def get_day_stats(prices):
    """
    Вычисляет статистику по списку цен.
    """

    if not prices:
        return None

    values = [item["cents_kwh"] for item in prices]

    minimum = min(values)
    maximum = max(values)
    average = sum(values) / len(values)

    min_item = min(
        prices,
        key=lambda item: item["cents_kwh"],
    )

    max_item = max(
        prices,
        key=lambda item: item["cents_kwh"],
    )

    return {
        "minimum": minimum,
        "minimum_time": min_item["time_text"],
        "maximum": maximum,
        "maximum_time": max_item["time_text"],
        "average": average,
        "intervals": len(prices),
    }


if __name__ == "__main__":
    print()
    print("TODAY")
    print("------------------------------------")

    today_prices = get_today_hourly_prices()

    for item in today_prices:
        print(
            f"{item['time_text']}  "
            f"{item['cents_kwh']:6.2f} c/kWh  "
            f"{item['cents_kwh_vat']:6.2f} "
            f"c/kWh VAT"
        )

    today_stats = get_day_stats(today_prices)

    print("------------------------------------")

    if today_stats:
        print(f"Intervals: " f"{today_stats['intervals']}")

        print(
            f"Minimum: "
            f"{today_stats['minimum']:.2f} "
            f"c/kWh at "
            f"{today_stats['minimum_time']}"
        )

        print(
            f"Maximum: "
            f"{today_stats['maximum']:.2f} "
            f"c/kWh at "
            f"{today_stats['maximum_time']}"
        )

        print(f"Average: " f"{today_stats['average']:.2f} " f"c/kWh")

    print()
    print("TOMORROW")
    print("------------------------------------")

    tomorrow_prices = get_tomorrow_hourly_prices()

    if tomorrow_prices:
        for item in tomorrow_prices:
            print(f"{item['time_text']}  " f"{item['cents_kwh']:6.2f} c/kWh")

        tomorrow_stats = get_day_stats(tomorrow_prices)

        print("------------------------------------")

        print(f"Intervals: " f"{tomorrow_stats['intervals']}")

        print(
            f"Minimum: "
            f"{tomorrow_stats['minimum']:.2f} "
            f"c/kWh at "
            f"{tomorrow_stats['minimum_time']}"
        )

        print(
            f"Maximum: "
            f"{tomorrow_stats['maximum']:.2f} "
            f"c/kWh at "
            f"{tomorrow_stats['maximum_time']}"
        )

        print(f"Average: " f"{tomorrow_stats['average']:.2f} " f"c/kWh")

    else:
        print("Tomorrow prices are not available yet.")
