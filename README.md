# ⚡ ElectricityTray

**ElectricityTray** is a lightweight Windows system tray application for monitoring Estonia's electricity market prices.

The application retrieves electricity price data from **Elering Estfeed** and displays current, upcoming, daily and next-day prices directly from the Windows notification area.

## Features

- ⚡ Current 15-minute electricity price
- ⏭ Next 15-minute price
- 📊 Interactive price charts
- 🕒 Current-time indicator on today's chart
- 📅 Today and tomorrow price views
- 🔍 Price information on mouse hover
- 📋 Detailed 15-minute price tables
- 📈 Adaptive vertical price scale
- 🔔 Automatic monitoring for tomorrow's prices
- 🔄 Background price updates
- 🖱 Open the panel with a tray icon click
- 🔒 Single-instance protection
- 💾 Persistent user settings
- 🌐 Multilingual interface

## Screenshot

![ElectricityTray interface](docs/screenshot.PNG)

## Languages

ElectricityTray currently supports:

- 🇪🇪 Eesti
- 🇬🇧 English
- 🇷🇺 Русский

The language can be changed from either the system tray menu or the selector in the main panel.

The selected language is remembered between application restarts.

## Interface

The main panel displays two daily charts:

**Today**

The complete 24-hour electricity price profile with a vertical marker showing the current time.

**Tomorrow**

Tomorrow's prices are displayed as soon as they become available from Elering.

The application periodically checks for newly published next-day prices.

Both charts use 15-minute intervals.

### Interactive price display

Move the mouse pointer over a chart to see the price for the corresponding 15-minute interval.

The tooltip includes:

- time interval;
- electricity price;
- price including VAT.

### Price tables

Use the **Show table** button to display detailed 15-minute price tables for today and tomorrow.

## Data source

Electricity price data is retrieved from the public **Elering Estfeed API**.

ElectricityTray is an independent application and is not affiliated with or endorsed by Elering.

## Installation

Download the latest Windows executable from the GitHub **Releases** section:

```text
ElectricityTray_<version>.exe
```

For example:

```text
ElectricityTray_1.1.0.exe
```

No Python installation is required when using the packaged executable.

Run the application and the ElectricityTray icon will appear in the Windows notification area.

## Building from source

### Requirements

- Windows 10 or later
- Python
- PowerShell

Clone the repository and create a Python virtual environment.

Install the required dependencies and activate the environment.

The project uses a single version source:

```text
version.txt
```

Example:

```text
1.1.0
```

Build the executable with:

```powershell
.\build.ps1
```

The build script automatically:

- reads the application version from `version.txt`;
- generates Windows version metadata;
- applies the ElectricityTray icon;
- cleans previous build artifacts;
- packages the application with PyInstaller;
- creates a versioned executable.

The resulting file is placed in:

```text
dist\ElectricityTray_<version>.exe
```

## Project structure

```text
ElectricityTray/
│
├── assets/
│   ├── ElectricityTray.ico
│   └── ElectricityTray.png
│
├── docs/
│   └── screenshot.PNG
│
├── main.py
├── tray.py
├── panel.py
├── elering.py
├── config.py
├── i18n.py
├── settings.py
│
├── version.txt
├── build.ps1
├── README.md
├── LICENS
└── .gitignore
```

## Versioning

ElectricityTray uses semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Example:

```text
1.1.0
```

Git release tags use the format:

```text
v1.1.0
```

## Current release

**ElectricityTray 1.1.0**

Major features in this release include:

- 15-minute electricity price monitoring;
- today and tomorrow charts;
- interactive price tooltips;
- detailed price tables;
- automatic next-day price monitoring;
- multilingual RU / EN / ET interface;
- persistent language settings;
- Windows executable packaging;
- versioned build system.

## Platform

Currently supported:

- Windows 10
- Windows 11

## License

This project is licensed under the MIT License.

See the `LICENSE` file for details.