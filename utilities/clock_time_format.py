def parse_start_time(time_str):
    """Parse 'HH:MM' string to total seconds. Returns 0 on failure."""
    try:
        parts = time_str.strip().split(":")
        return int(parts[0]) * 3600 + int(parts[1]) * 60
    except Exception:
        return 0


def format_clock_time(abs_seconds):
    """Format absolute seconds as 'HH:MMh', wrapping at 24 h."""
    h = int(abs_seconds // 3600) % 24
    m = int((abs_seconds % 3600) // 60)
    return f"{h:02d}:{m:02d}h"
