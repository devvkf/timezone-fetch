# timezonefetch

A tiny, dependency-free `neofetch`-style command that displays your computer's local clock and timezone information.

```text
  09:42       user@host
              ---------
              Timezone  Europe/Berlin
              Region    (UTC+01:00) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna
              Local time 09:42:18  (9:42:18 AM)
              Date      Monday, 20 October 2025  ·  2025-10-20
              Offset    UTC+02:00  ·  GMT+2
              UTC time  07:42:18
              DST       Yes  ·  daylight saving
```

## Features

- Seven-segment block clock for the current local time
- Local timezone and friendly Windows timezone name
- Local time in 24-hour and 12-hour formats
- Long and ISO-formatted dates
- UTC/GMT offset and current UTC time
- Daylight saving time status
- ANSI color output when running in an interactive terminal
- Plain output for scripts and pipes
- Python standard library only

## Requirements

- Python 3.9 or newer
- Windows is supported directly; macOS and Linux use Python's local timezone information as a fallback

## Usage

Clone the repository and run the script:

```bash
git clone https://github.com/devvkf/timezone-fetch.git
cd timezone-fetch
python timezonefetch.py
```

On Unix-like systems, you can also run it directly:

```bash
chmod +x timezonefetch.py
./timezonefetch.py
```

### Options

```text
--no-color   Keep the clock art but disable ANSI colors
--plain      Print Label: value lines only, without clock art
```

Examples:

```bash
python timezonefetch.py --no-color
python timezonefetch.py --plain
python timezonefetch.py --plain | grep 'Offset'
```

Color output is automatically disabled when stdout is not a TTY or when the `NO_COLOR` environment variable is set.

## Project layout

```text
timezone-fetch/
├── timezonefetch.py   # Application and command-line interface
├── README.md          # Documentation
└── .gitignore         # Local Python/tooling exclusions
```

## Development

There are no third-party dependencies or build steps. Run the following quick checks from the repository root:

```bash
python -m py_compile timezonefetch.py
python timezonefetch.py --plain
```
