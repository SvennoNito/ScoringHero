"""Dialog button rows: the primary action sits on the right, after Cancel, on every platform."""

from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QVBoxLayout


def test_ok_is_right_of_cancel_in_standard_button_boxes(loaded_ui):
    dialog = QDialog()
    box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    QVBoxLayout(dialog).addWidget(box)
    dialog.resize(400, 120)
    dialog.show()
    QApplication.processEvents()

    ok, cancel = box.button(QDialogButtonBox.Ok), box.button(QDialogButtonBox.Cancel)
    assert cancel.geometry().right() < ok.geometry().left()
    assert ok.geometry().right() > box.width() - 40  # flush right
    dialog.close()
