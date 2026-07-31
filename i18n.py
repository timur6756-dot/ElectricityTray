LANGUAGES = ("ru", "en", "et")

LANGUAGE_NAMES = {
    "ru": "Русский",
    "en": "English",
    "et": "Eesti",
}

LANGUAGE_SHORT = {
    "ru": "RU",
    "en": "EN",
    "et": "ET",
}


TRANSLATIONS = {
    "ru": {
        "window_title": "Electricity Estonia",
        "open_panel": "Открыть панель",
        "refresh": "Обновить",
        "exit": "Выход",
        "language": "Язык",
        "current_exchange_price": "текущая биржевая цена",
        "current_interval": "Текущий интервал: {start}–{end}",
        "next_15": "Следующие 15 мин: {price:.2f} c/kWh",
        "next_unavailable": "Следующая цена недоступна",
        "today": "Сегодня",
        "tomorrow": "Завтра",
        "minimum": "Мин",
        "maximum": "Макс",
        "average": "Средняя",
        "at": "в",
        "today_stats": (
            "Мин: {minimum:.2f} c/kWh в {minimum_time}"
            "   |   "
            "Макс: {maximum:.2f} c/kWh в {maximum_time}"
            "   |   "
            "Средняя: {average:.2f} c/kWh"
        ),
        "tomorrow_not_published": "Цены на завтра ещё не опубликованы",
        "tomorrow_intervals": "Опубликовано интервалов: "
        "{count} из 96 ({percent:.1f}%)",
        "tomorrow_stats": (
            "Опубликовано интервалов: "
            "{count} из 96 ({percent:.1f}%)"
            "   |   "
            "Мин: {minimum:.2f} c/kWh в {minimum_time}"
            "   |   "
            "Макс: {maximum:.2f} c/kWh в {maximum_time}"
            "   |   "
            "Средняя: {average:.2f} c/kWh"
        ),
        "data_unavailable": "Данные недоступны",
        "no_data": "Данных пока нет",
        "last_update": "Последнее обновление: {time}"
        "   ·   "
        "следующее на границе 15 мин",
        "show_table": "Показать таблицу",
        "hide_table": "Скрыть таблицу",
        "interval": "Интервал",
        "price": "Цена, c/kWh",
        "price_vat": "С НДС, c/kWh",
        "with_vat": "с НДС",
        "tray_now": "Сейчас: {price:.2f} c/kWh",
        "tray_next": "Следующие 15 мин: {price:.2f} c/kWh",
        "tray_tomorrow": "Завтра опубликовано: {count}/96",
        "tray_tomorrow_none": "Завтра: данных пока нет",
        "new_prices_title": "Electricity Estonia",
        "new_prices": "Опубликованы новые цены на завтра: " "{count}/96 интервалов",
        "update_error": "Ошибка обновления: {error}",
        "price_error": "Ошибка цены: {error}",
    },
    "en": {
        "window_title": "Electricity Estonia",
        "open_panel": "Open panel",
        "refresh": "Refresh",
        "exit": "Exit",
        "language": "Language",
        "current_exchange_price": "current exchange price",
        "current_interval": "Current interval: {start}–{end}",
        "next_15": "Next 15 min: {price:.2f} c/kWh",
        "next_unavailable": "Next price unavailable",
        "today": "Today",
        "tomorrow": "Tomorrow",
        "minimum": "Min",
        "maximum": "Max",
        "average": "Average",
        "at": "at",
        "today_stats": (
            "Min: {minimum:.2f} c/kWh at {minimum_time}"
            "   |   "
            "Max: {maximum:.2f} c/kWh at {maximum_time}"
            "   |   "
            "Average: {average:.2f} c/kWh"
        ),
        "tomorrow_not_published": "Tomorrow's prices have not been published yet",
        "tomorrow_intervals": "Published intervals: " "{count} of 96 ({percent:.1f}%)",
        "tomorrow_stats": (
            "Published intervals: "
            "{count} of 96 ({percent:.1f}%)"
            "   |   "
            "Min: {minimum:.2f} c/kWh at {minimum_time}"
            "   |   "
            "Max: {maximum:.2f} c/kWh at {maximum_time}"
            "   |   "
            "Average: {average:.2f} c/kWh"
        ),
        "data_unavailable": "Data unavailable",
        "no_data": "No data yet",
        "last_update": "Last update: {time}"
        "   ·   "
        "next update at the 15-minute boundary",
        "show_table": "Show table",
        "hide_table": "Hide table",
        "interval": "Interval",
        "price": "Price, c/kWh",
        "price_vat": "VAT incl., c/kWh",
        "with_vat": "VAT incl.",
        "tray_now": "Now: {price:.2f} c/kWh",
        "tray_next": "Next 15 min: {price:.2f} c/kWh",
        "tray_tomorrow": "Tomorrow published: {count}/96",
        "tray_tomorrow_none": "Tomorrow: no data yet",
        "new_prices_title": "Electricity Estonia",
        "new_prices": "New prices for tomorrow published: " "{count}/96 intervals",
        "update_error": "Update error: {error}",
        "price_error": "Price error: {error}",
    },
    "et": {
        "window_title": "Electricity Estonia",
        "open_panel": "Ava paneel",
        "refresh": "Värskenda",
        "exit": "Välju",
        "language": "Keel",
        "current_exchange_price": "praegune börsihind",
        "current_interval": "Praegune intervall: {start}–{end}",
        "next_15": "Järgmised 15 min: {price:.2f} c/kWh",
        "next_unavailable": "Järgmine hind pole saadaval",
        "today": "Täna",
        "tomorrow": "Homme",
        "minimum": "Min",
        "maximum": "Maks",
        "average": "Keskmine",
        "at": "kell",
        "today_stats": (
            "Min: {minimum:.2f} c/kWh kell {minimum_time}"
            "   |   "
            "Maks: {maximum:.2f} c/kWh kell {maximum_time}"
            "   |   "
            "Keskmine: {average:.2f} c/kWh"
        ),
        "tomorrow_not_published": "Homse päeva hindu pole veel avaldatud",
        "tomorrow_intervals": "Avaldatud intervalle: " "{count} / 96 ({percent:.1f}%)",
        "tomorrow_stats": (
            "Avaldatud intervalle: "
            "{count} / 96 ({percent:.1f}%)"
            "   |   "
            "Min: {minimum:.2f} c/kWh kell {minimum_time}"
            "   |   "
            "Maks: {maximum:.2f} c/kWh kell {maximum_time}"
            "   |   "
            "Keskmine: {average:.2f} c/kWh"
        ),
        "data_unavailable": "Andmed pole saadaval",
        "no_data": "Andmeid veel pole",
        "last_update": "Viimane uuendus: {time}"
        "   ·   "
        "järgmine uuendus 15 minuti piiril",
        "show_table": "Näita tabelit",
        "hide_table": "Peida tabel",
        "interval": "Intervall",
        "price": "Hind, c/kWh",
        "price_vat": "KM-ga, c/kWh",
        "with_vat": "KM-ga",
        "tray_now": "Praegu: {price:.2f} c/kWh",
        "tray_next": "Järgmised 15 min: {price:.2f} c/kWh",
        "tray_tomorrow": "Homme avaldatud: {count}/96",
        "tray_tomorrow_none": "Homme: andmeid veel pole",
        "new_prices_title": "Electricity Estonia",
        "new_prices": "Uued homsed hinnad avaldatud: " "{count}/96 intervalli",
        "update_error": "Uuendamise viga: {error}",
        "price_error": "Hinna viga: {error}",
    },
}


def normalize_language(language):
    if language in LANGUAGES:
        return language

    return "ru"


def t(key, language="ru", **kwargs):
    language = normalize_language(language)

    text = TRANSLATIONS.get(
        language,
        TRANSLATIONS["ru"],
    ).get(
        key,
        TRANSLATIONS["ru"].get(key, key),
    )

    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text

    return text
