import json
import os
from pathlib import Path

from i18n import normalize_language

APP_NAME = "ElectricityTray"


def get_settings_directory():
    """
    Возвращает:
    %APPDATA%\\ElectricityTray
    """

    appdata = os.environ.get("APPDATA")

    if appdata:
        directory = Path(appdata) / APP_NAME

    else:
        directory = Path.home() / ".electricitytray"

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def get_settings_file():
    return get_settings_directory() / "settings.json"


def load_settings():
    """Загружает пользовательские настройки."""

    path = get_settings_file()

    defaults = {
        "language": "ru",
    }

    if not path.exists():
        return defaults.copy()

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return defaults.copy()

    language = normalize_language(
        data.get(
            "language",
            "ru",
        )
    )

    return {
        "language": language,
    }


def save_settings(settings):
    """Сохраняет настройки."""

    path = get_settings_file()

    try:
        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                settings,
                file,
                ensure_ascii=False,
                indent=2,
            )

    except OSError:
        pass


def save_language(language):
    """Сохраняет выбранный язык."""

    language = normalize_language(language)

    settings = load_settings()

    settings["language"] = language

    save_settings(settings)
