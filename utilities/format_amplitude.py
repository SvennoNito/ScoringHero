def format_amplitude(value):
    """Format an amplitude as an int when it is a whole number, else as-is."""
    return int(value) if value == int(value) else value
