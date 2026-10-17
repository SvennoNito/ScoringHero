"""Scene 11: export the sleep report (PDF) from the Export menu.

The options dialog is shown and clicked through: "Preview" first (renders page 1 of the
generated PDF onto the frame for a few seconds), then "Generate Report". The native save
dialog is mocked to return `<video_dir>/sleep_report.pdf`. Needs Stages from an earlier scene
(s06 GSSC).
Hands over: ctx.state["s11_report"] = path of the PDF.
"""

import os
from unittest import mock

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QLabel, QMessageBox

from export import export_sleep_report as report

PDF_NAME = "sleep_report.pdf"
PREVIEW_SECONDS = 5.0


def _show_pdf_page(ctx, path):
    """Render page 1 of the PDF at `path` and show it as a top-level QLabel positioned over
    the window: ctx._compose() composites every visible top-level widget besides the window
    itself, so this is captured by the normal frame grab exactly like the s05 magnitude
    response dialog, with no Context changes needed."""
    doc = QPdfDocument()
    doc.load(path)
    point_size = doc.pagePointSize(0)
    image = doc.render(0, QSize(round(point_size.width() * 2), round(point_size.height() * 2)))

    label = QLabel()
    label.setPixmap(QPixmap.fromImage(image).scaledToHeight(round(ctx.window.height() * 0.85), Qt.SmoothTransformation))
    label.adjustSize()
    area = ctx.window.geometry()
    label.move(area.center().x() - label.width() // 2, area.center().y() - label.height() // 2)
    label.show()
    ctx.app.processEvents()
    ctx.caption("Preview: page 1 of the generated report")
    ctx.wait(PREVIEW_SECONDS)
    label.close()
    doc.close()


def run(ctx):
    ctx.wait_idle()
    path = os.path.join(ctx.video_dir, PDF_NAME)
    if os.path.exists(path):
        os.remove(path)
    ctx.state["s11_report"] = path
    ctx.state["s11_preview_rendered"] = False

    def film_options(dialog):
        """Replaces QDialog.exec: show the options, preview page 1, click Generate Report, report the result."""
        dialog.show()
        ctx.app.processEvents()  # the dialog reaches its final size only once shown
        area = ctx.window.geometry()
        dialog.move(area.center().x() - dialog.width() // 2, max(area.top() + 10, area.center().y() - dialog.height() // 2))
        ctx.caption("Choose what goes into the report")
        ctx.wait(1.5)

        # the system viewer call (QDesktopServices.openUrl) is mocked: no real viewer in this
        # headless offscreen environment; the preview PDF itself is still generated on disk
        with mock.patch.object(QDesktopServices, "openUrl", lambda *a, **k: True), \
                mock.patch.object(QMessageBox, "critical", lambda *a, **k: QMessageBox.Ok):
            ctx.click(ctx.button(dialog, "Preview"), duration=0.8)
        preview_path = dialog._preview_files[-1] if dialog._preview_files else None
        assert preview_path and os.path.isfile(preview_path), "Preview did not generate a PDF"
        _show_pdf_page(ctx, preview_path)
        ctx.state["s11_preview_rendered"] = True
        ctx.state["s11_preview_rendered_at"] = ctx.frames_written

        ctx.caption("Choose what goes into the report")
        ctx.click(ctx.button(dialog, "Generate Report"), duration=0.8)
        return dialog.result()

    ctx.caption("Export: sleep report (PDF)")
    with ctx.file_dialogs(save=path), \
            mock.patch.object(report._ReportOptionsDialog, "exec", film_options), \
            mock.patch.object(QMessageBox, "information", lambda *a, **k: QMessageBox.Ok):
        ctx.click_menu("action_export_sleep_report")
        ctx.wait(0.5)
    ctx.state["s11_pdf_written_at"] = ctx.frames_written
    ctx.caption("The sleep report is saved as a PDF")
    ctx.wait(2.0)


def check(ctx):
    assert ctx.state.get("s11_preview_rendered"), "sleep report preview was not rendered"
    assert ctx.state["s11_preview_rendered_at"] < ctx.state["s11_pdf_written_at"], \
        "preview was not rendered before the report was generated"
    path = ctx.state["s11_report"]
    assert os.path.isfile(path), f"sleep report PDF missing: {path}"
    with open(path, "rb") as f:
        assert f.read(5) == b"%PDF-", "sleep report is not a PDF"
    assert os.path.getsize(path) > 5000, "sleep report PDF is suspiciously small"
