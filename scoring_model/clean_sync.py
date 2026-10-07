def sync_clean(scoring, before, after):
    """Keep the Scoring clean flag consistent with slot 0. `before` and `after` are the
    0-based epochs covered by slot 0 around an edit (`Events.artefact_epochs()`); `before`
    is empty after a rebuild or import. Newly covered epochs become unclean, newly
    uncovered ones clean, every other epoch is left alone."""
    scoring.set_clean(sorted(after - before), 0)
    scoring.set_clean(sorted(before - after), 1)
