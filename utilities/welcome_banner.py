import sys
from importlib.metadata import version

ISSUES_URL = "https://github.com/SvennoNito/ScoringHero/issues"
WIDTH = 68


def _line(text=""):
    return "║" + text.center(WIDTH) + "║"


def build_welcome_banner(version_string):
    lines = [
        "╔" + "═" * WIDTH + "╗",
        _line(),
        _line("✦ · ☾ · ★ · ✿ · ★ · ☾ · ✦"),
        _line(),
        _line(f"♥  Welcome to ScoringHero v.{version_string}  ♥"),
        _line(),
        _line("★  We are so happy to have you here  ★"),
        _line("Happy scoring, and sweet dreams to all your recordings ☾"),
        _line(),
        _line("✿ · · · · · · · · · · · · · · · · · · · · · · · ✿"),
        _line(),
        _line("Found a bug or wish for a new feature?"),
        _line("♪  Please post it on the issue tracker  ♪"),
        _line(),
        _line(ISSUES_URL),
        _line(),
        _line("✦ · ☾ · ★ · ✿ · ★ · ☾ · ✦"),
        _line(),
        "╚" + "═" * WIDTH + "╝",
    ]
    return "\n".join(lines)


def print_welcome_banner():
    """Print the welcome banner to the console window (no-op when there is none)."""
    if sys.stdout is None:
        return
    # The Windows console defaults to cp1252, which cannot encode the symbols
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("\n" + build_welcome_banner(version("scoringhero")) + "\n", flush=True)
