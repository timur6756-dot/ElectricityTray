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


def get_raw_day_prices(
    target_date,
    resolution="fifteen_minutes",
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
    resolution="fifteen_minutes",
):
    """Преобразует ответ API в удобный список."""

    raw_data = get_raw_day_prices(
        target_date,
        resolution=resolution,
    )

    result = []

    for item in raw_data:
        from_time = datetime.fromisoformat(item["fromDateTime"])

        to_time = datetime.fromisoformat(item["toDateTime"])

        result.append(
            {
                "date": target_date,
                "time": from_time,
                "end_time": to_time,
                "time_text": from_time.strftime("%H:%M"),
                "interval_text": (
                    f"{from_time:%H:%M}–" f"{to_time + timedelta(microseconds=1):%H:%M}"
                ),
                "cents_kwh": item["centsPerKwh"],
                "cents_kwh_vat": item["centsPerKwhWithVat"],
                "eur_mwh": item["eurPerMwh"],
                "eur_mwh_vat": item["eurPerMwhWithVat"],
            }
        )

    return result


def get_current_and_next_estonia_price():
    """Возвращает текущую и следующую 15-минутную цену."""

    now = datetime.now(ESTONIA_TZ)

    today = now.date()

    prices = normalize_day_prices(
        today,
        resolution="fifteen_minutes",
    )

    current_item = None
    next_item = None

    for index, item in enumerate(prices):
        start = item["time"]
        end = item["end_time"]

        if start <= now <= end:
            current_item = item

            if index + 1 < len(prices):
                next_item = prices[index + 1]

            break

    if current_item is None:
        raise RuntimeError("Current Estonia price not found")

    result = {
        "current": {
            "timestamp": current_item["time"].isoformat(),
            "eur_mwh": current_item["eur_mwh"],
            "cents_kwh": current_item["cents_kwh"],
            "cents_kwh_vat": current_item["cents_kwh_vat"],
        },
        "next": None,
    }

    if next_item is not None:
        result["next"] = {
            "timestamp": next_item["time"].isoformat(),
            "eur_mwh": next_item["eur_mwh"],
            "cents_kwh": next_item["cents_kwh"],
            "cents_kwh_vat": next_item["cents_kwh_vat"],
        }

    return result


def get_today_hourly_prices():
    """
    Совместимость с tray/panel.
    Теперь возвращает 15-минутные цены.
    """

    today = datetime.now(ESTONIA_TZ).date()

    return normalize_day_prices(
        today,
        resolution="fifteen_minutes",
    )


def get_tomorrow_hourly_prices():
    """
    Совместимость с существующим кодом.
    Теперь возвращает 15-минутные цены завтра.
    """

    tomorrow = datetime.now(ESTONIA_TZ).date() + timedelta(days=1)

    try:
        return normalize_day_prices(
            tomorrow,
            resolution="fifteen_minutes",
        )

    except requests.HTTPError:
        return []


def get_day_stats(prices):
    """Вычисляет статистику по списку цен."""

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
        "average": (sum(values) / len(values)),
        "intervals": len(prices),
    }


if __name__ == "__main__":
    today = get_today_hourly_prices()
    tomorrow = get_tomorrow_hourly_prices()

    print()
    print("TODAY 15-MINUTE")
    print("------------------------------")
    print("Intervals:", len(today))

    stats = get_day_stats(today)

    if stats:
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

    print()
    print("TOMORROW 15-MINUTE")
    print("------------------------------")
    print("Intervals:", len(tomorrow))
