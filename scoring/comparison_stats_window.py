import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


_STAGE_ORDER = ["Wake", "N1", "N2", "N3", "REM", "Inconclusive", None]


def _cohen_kappa(y1, y2, labels):
    label_to_idx = {l: i for i, l in enumerate(labels)}
    n = len(y1)
    k = len(labels)
    confusion = np.zeros((k, k), dtype=int)

    for a, b in zip(y1, y2):
        i = label_to_idx.get(a, -1)
        j = label_to_idx.get(b, -1)
        if i >= 0 and j >= 0:
            confusion[i][j] += 1

    po = np.trace(confusion) / n if n > 0 else 0.0
    row_sums = confusion.sum(axis=1)
    col_sums = confusion.sum(axis=0)
    pe = np.dot(row_sums, col_sums) / (n * n) if n > 0 else 0.0
    kappa = (po - pe) / (1 - pe) if pe < 1.0 else 1.0
    return kappa, confusion, po


def comparison_stats_window(ui):
    n = min(len(ui.stages), len(ui.stages_ref))
    y1 = [s["stage"] for s in ui.stages[:n]]
    y2 = [s["stage"] for s in ui.stages_ref[:n]]

    # Build label list in canonical stage order, keeping only present ones
    present_set = set(y1) | set(y2)
    labels = [s for s in _STAGE_ORDER if s in present_set]
    label_strs = [s if s is not None else "Unscored" for s in labels]

    kappa, confusion, po = _cohen_kappa(y1, y2, labels)
    n_agree = int(round(po * n))
    pct_agree = po * 100

    dialog = QDialog()
    dialog.setWindowTitle("Scoring Agreement Statistics")
    dialog.resize(520, 420)

    layout = QVBoxLayout()
    layout.setSpacing(8)

    layout.addWidget(QLabel(f"<b>Epochs compared:</b> {n}"))
    layout.addWidget(QLabel(
        f"<b>Overall agreement:</b> {pct_agree:.1f}%  ({n_agree} / {n} epochs)"
    ))
    kappa_interp = _kappa_label(kappa)
    layout.addWidget(QLabel(
        f"<b>Cohen's κ:</b> {kappa:.3f}  <i>({kappa_interp})</i>"
    ))
    layout.addWidget(QLabel(
        f"<b>Disagreements:</b> {len(ui.disagreement_epochs)} epochs"
    ))

    layout.addWidget(QLabel(
        "<b>Confusion matrix</b> "
        "(rows = primary scoring, columns = comparison scoring):"
    ))

    k = len(labels)
    table = QTableWidget(k, k)
    table.setHorizontalHeaderLabels(label_strs)
    table.setVerticalHeaderLabels(label_strs)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    for i in range(k):
        for j in range(k):
            val = confusion[i][j]
            item = QTableWidgetItem(str(val))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if i == j:
                item.setBackground(QColor("#d4edda"))
            elif val > 0:
                item.setBackground(QColor("#f8d7da"))
            table.setItem(i, j, item)

    layout.addWidget(table)

    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)

    dialog.setLayout(layout)
    dialog.exec()


def _kappa_label(k):
    if k < 0:
        return "poor"
    if k < 0.20:
        return "slight"
    if k < 0.40:
        return "fair"
    if k < 0.60:
        return "moderate"
    if k < 0.80:
        return "substantial"
    return "almost perfect"
