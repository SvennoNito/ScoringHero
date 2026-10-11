"""Scene 9: export the sleep report (PDF) from the Export menu.

The options dialog is shown and clicked through; the native save dialog is mocked to return
`<video_dir>/sleep_report.pdf`. Needs Stages from an earlier scene (s04 GSSC).
Hands over: ctx.state["s09_report"] = path of the PDF.
"""

import os
from unittest import mock

from PySide6.QtWidgets import QMessageBox, QPushButton

from export import export_sleep_report as report

PDF_NAME = "sleep_report.pdf"


def run(ctx):
    ui = ctx.ui
    ctx.wait_until(lambda: not getattr(ui, "_busy_runners", None))  # the busy indicator swallows mouse input
    path = os.path.join(ctx.video_dir, PDF_NAME)
    if os.path.exists(path):
        os.remove(path)
    ctx.state["s09_report"] = path

    def film_options(dialog):
        """Replaces QDialog.exec: show the options, click Generate Report, report the result."""
        dialog.move(ctx.window.geometry().center() - dialog.rect().center())
        dialog.show()
        ctx.caption("Choose what goes into the report")
        ctx.wait(1.5)
        button = next(b for b in dialog.findChildren(QPushButton) if b.text() == "Generate Report")
        ctx.click(button, duration=0.8)
        return dialog.result()

    ctx.caption("Export: sleep report (PDF)")
    with ctx.file_dialogs(save=path), \
            mock.patch.object(report._ReportOptionsDialog, "exec", film_options), \
            mock.patch.object(QMessageBox, "information", lambda *a, **k: QMessageBox.Ok):
        ctx.click_menu("action_export_sleep_report")
        ctx.wait(0.5)
    ctx.caption("The sleep report is saved as a PDF")
    ctx.wait(2.0)


def check(ctx):
    path = ctx.state["s09_report"]
    assert os.path.isfile(path), f"sleep report PDF missing: {path}"
    with open(path, "rb") as f:
        assert f.read(5) == b"%PDF-", "sleep report is not a PDF"
    assert os.path.getsize(path) > 5000, "sleep report PDF is suspiciously small"
