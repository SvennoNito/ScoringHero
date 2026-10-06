"""Dialog layer of scoring_model.resolve: one warning per problem."""

from PySide6.QtWidgets import QMessageBox

from scoring_model.resolve import resolve

_MAX_LISTED = 10

_TEXT = {
    "unknown": "The scoring contains stages or codes that are not recognised: {names}.\n\n"
    "Replace them with unscored, or cancel.",
    "longer_1": "The scoring has 1 epoch more than the recording. The last (partial) epoch is dropped.",
    "shorter_1": "The scoring has 1 epoch fewer than the recording. The last epoch is copied.",
    "longer_n": "The scoring has {n} epochs more than the recording (scoring {loaded}, recording {rec}).\n\n"
    "Truncate it to the recording length, or cancel.",
    "shorter_n": "The scoring has {n} epochs fewer than the recording (scoring {loaded}, recording {rec}).\n\n"
    "Copy its last epoch until the length matches, or cancel.",
}
_BUTTON = {"ok": "OK", "truncate": "Truncate", "copy_last": "Copy last epoch", "replace": "Replace with unscored"}


def _ask_factory(parent, n_epochs):
    def ask(question):
        p = question.problems
        names = ", ".join(p.unknown[:_MAX_LISTED]) + (" ..." if len(p.unknown) > _MAX_LISTED else "")
        text = _TEXT[question.kind].format(
            names=names, n=abs(p.diff), loaded=n_epochs + p.diff, rec=n_epochs
        )
        box = QMessageBox(parent)
        box.setIcon(QMessageBox.Warning)
        box.setWindowTitle("Scoring does not match the recording")
        box.setText(text)
        buttons = {box.addButton(_BUTTON[c], QMessageBox.AcceptRole): c for c in question.choices}
        if question.choices != ("ok",):
            box.addButton("Cancel", QMessageBox.RejectRole)
        box.exec()
        return buttons.get(box.clickedButton())
    return ask


def resolve_loaded(parent, loaded, n_epochs, epoch_length_s):
    """Scoring fitted to the recording, or None if the user cancelled. The caller
    decides what cancel means. A notice-only box (1-off) closed with Esc still
    returns the scoring."""
    ask = _ask_factory(parent, n_epochs)

    def ask_or_ok(question):
        answer = ask(question)
        return "ok" if answer is None and question.choices == ("ok",) else answer

    return resolve(loaded, n_epochs, epoch_length_s, ask_or_ok)
