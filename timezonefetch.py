#!/usr/bin/env python3
"""timezonefetch - a neofetch-style panel for this PC's clock settings.

Shows the machine's timezone, local time, UTC/GMT offset and date, next to a
seven-segment clock drawn with block characters. Standard library only.

Usage:
    python timezonefetch.py [--no-color] [--plain]

Options:
    --no-color   Keep the art but drop ANSI colors.
    --plain      Print "Label: value" lines only (pipe-friendly).
"""

import argparse
import datetime as dt
import getpass
import os
import socket
import sys
import time

# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
CYAN = "\x1b[36m"
BRIGHT_CYAN = "\x1b[96m"


def enable_ansi() -> None:
    """Turn on VT escape processing for the legacy Windows console."""
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def paint(text: str, code: str, enabled: bool) -> str:
    return f"{code}{text}{RESET}" if enabled else text


# ---------------------------------------------------------------------------
# Clock art (3x5 seven-segment glyphs)
# ---------------------------------------------------------------------------

GLYPHS = {
    "0": ("███", "█ █", "█ █", "█ █", "███"),
    "1": (" █ ", "██ ", " █ ", " █ ", "███"),
    "2": ("███", "  █", "███", "█  ", "███"),
    "3": ("███", "  █", "███", "  █", "███"),
    "4": ("█ █", "█ █", "███", "  █", "  █"),
    "5": ("███", "█  ", "███", "  █", "███"),
    "6": ("███", "█  ", "███", "█ █", "███"),
    "7": ("███", "  █", "  █", "  █", "  █"),
    "8": ("███", "█ █", "███", "█ █", "███"),
    "9": ("███", "█ █", "███", "  █", "███"),
    ":": ("   ", " █ ", "   ", " █ ", "   "),
}


def clock_art(now: dt.datetime) -> list[str]:
    """Render the current HH:MM as five rows of block characters."""
    rows = [""] * 5
    for char in now.strftime("%H:%M"):
        glyph = GLYPHS[char]
        for i in range(5):
            rows[i] += glyph[i] + " "
    return [row.rstrip() for row in rows]


# ---------------------------------------------------------------------------
# Timezone + formatting
# ---------------------------------------------------------------------------

TZ_INFO_KEY = r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation"
TZ_DB_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Time Zones"


def windows_timezone() -> tuple[str, str | None]:
    """Return (timezone id, friendly display name) from the registry."""
    tz_id = None
    display = None

    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, TZ_INFO_KEY) as key:
                tz_id = winreg.QueryValueEx(key, "TimeZoneKeyName")[0]
        except OSError:
            pass

        if tz_id:
            try:
                import winreg

                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE, f"{TZ_DB_KEY}\\{tz_id}"
                ) as key:
                    display = winreg.QueryValueEx(key, "Display")[0]
            except OSError:
                pass

    if not tz_id:
        # Portable fallback: tzname() is the Windows zone name on CPython.
        tz_id = time.tzname[0] if time.tzname else "Local time"

    return tz_id, display


def offset_labels(delta: dt.timedelta) -> tuple[str, str]:
    """Return ("UTC+07:00", "GMT+7") for the given offset."""
    minutes = int(delta.total_seconds()) // 60
    sign = "+" if minutes >= 0 else "-"
    hours, mins = divmod(abs(minutes), 60)

    utc = f"UTC{sign}{hours:02d}:{mins:02d}"
    gmt = f"GMT{sign}{hours}" + (f":{mins:02d}" if mins else "")
    return utc, gmt


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def build_rows(now: dt.datetime) -> list[tuple[str, str, str]]:
    """Return (label, value, dim suffix) rows describing the clock."""
    tz_id, display = windows_timezone()
    offset = now.utcoffset() or dt.timedelta(0)
    utc_label, gmt_label = offset_labels(offset)

    local_24 = now.strftime("%H:%M:%S")
    local_12 = now.strftime("%I:%M:%S %p").lstrip("0")
    date_long = now.strftime("%A, %d %B %Y")
    date_iso = now.strftime("%Y-%m-%d")
    utc_time = now.astimezone(dt.timezone.utc).strftime("%H:%M:%S")
    dst = bool(now.dst())

    rows = [
        ("Timezone", tz_id, ""),
        ("Region", display or "(UTC offset applied by the OS)", ""),
        ("Local time", f"{local_24}  ", f"({local_12})"),
        ("Date", date_long, f"  ·  {date_iso}"),
        ("Offset", utc_label, f"  ·  {gmt_label}"),
        ("UTC time", utc_time, ""),
        ("DST", "Yes" if dst else "No",
         "  ·  daylight saving" if dst else "  ·  standard time"),
    ]
    return rows


def render_panel(rows, now, color: bool) -> None:
    art = clock_art(now)
    user = getpass.getuser()
    host = socket.gethostname()

    if color:
        header = (
            paint(user, BRIGHT_CYAN, True)
            + paint("@", DIM, True)
            + paint(host, BRIGHT_CYAN, True)
        )
    else:
        header = f"{user}@{host}"

    rule = paint("─" * len(f"{user}@{host}"), DIM, color)
    label_width = max(len(label) for label, _, _ in rows)
    art_width = max(len(line) for line in art)

    info = [header, rule]
    for label, value, suffix in rows:
        padded = f"{label:<{label_width}}"
        line = paint(padded, CYAN, color) + "  " + value
        if suffix:
            line += paint(suffix, DIM, color)
        info.append(line)

    for i in range(max(len(art), len(info))):
        left = art[i] if i < len(art) else ""
        right = info[i] if i < len(info) else ""
        if right:
            left = f"{left:<{art_width}}" if left else " " * art_width
            print(f"{paint(left, BRIGHT_CYAN, color)}   {right}")
        elif left:
            print(paint(left, BRIGHT_CYAN, color))
        else:
            print()


def render_plain(rows) -> None:
    for label, value, suffix in rows:
        print(f"{label}: {value}{suffix}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="timezonefetch",
        description="Show this PC's timezone, local time, UTC/GMT offset and date.",
    )
    parser.add_argument("--no-color", action="store_true", help="disable ANSI colors")
    parser.add_argument(
        "--plain", action="store_true", help="plain 'Label: value' output, no art"
    )
    args = parser.parse_args(argv)

    # Block characters need UTF-8 even when the output is redirected.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    now = dt.datetime.now().astimezone()
    rows = build_rows(now)

    color = (
        not args.no_color
        and not args.plain
        and "NO_COLOR" not in os.environ
        and sys.stdout.isatty()
    )

    if args.plain:
        render_plain(rows)
    else:
        if color:
            enable_ansi()
        print()
        render_panel(rows, now, color)
        print()

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        os._exit(0)
