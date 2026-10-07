def set_role(widget, role):
    """Tag `widget` with a QSS role (see `[role=...]` selectors in modern_theme.qss) and restyle it.
    role=None clears it."""
    widget.setProperty("role", role)
    widget.style().unpolish(widget)
    widget.style().polish(widget)
