from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QCheckBox,
    QDoubleSpinBox,
    QPushButton,
    QScrollArea,
    QWidget,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from filter.apply_filter import apply_filter


class FilterWindow(QDialog):
    filterApplied = Signal()

    def __init__(self, channel_config, sampling_rate, eeg_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter")
        self.resize(820, 500)
        self._channel_config = channel_config
        self._sampling_rate = sampling_rate
        self._eeg_data = eeg_data

        layout = QVBoxLayout(self)

        # Info label
        description = QLabel(
            "\u24d8 "
            "High-pass, low-pass, or notch-filter a given EEG channel using a"
            "Chebyshev Type 2 filter. The specified cutoff frequency is the "
            "\u221240\u202fdB stopband edge, not the \u22123\u202fdB point. "
            "Filters affect only the displayed EEG signal, not any power computations. "
            "Change filter parameters here. "
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # "Apply changes to all channels" checkbox
        self.apply_all_checkbox = QCheckBox("Apply changes to all channels")
        layout.addWidget(self.apply_all_checkbox)

        # Scroll area — QGridLayout ensures all columns align automatically
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(4)
        grid.setContentsMargins(6, 6, 6, 6)
        scroll_area.setWidget(grid_widget)

        bold_font = QFont()
        bold_font.setBold(True)

        def _hdr(text, align=Qt.AlignCenter):
            lbl = QLabel(text)
            lbl.setFont(bold_font)
            lbl.setAlignment(align)
            return lbl

        # Column indices
        C_CHAN = 0
        C_HP_EN, C_HP_CUT, C_HP_ORD = 1, 2, 3
        C_LP_EN, C_LP_CUT, C_LP_ORD = 4, 5, 6
        C_NT_EN, C_NT_CUT, C_NT_ORD = 7, 8, 9
        LAST_COL = 9

        # Row 0: filter-group super-headers (spanning 3 columns each)
        grid.addWidget(_hdr("High-pass filter"), 0, C_HP_EN, 1, 3, Qt.AlignCenter)
        grid.addWidget(_hdr("Low-pass filter"),  0, C_LP_EN, 1, 3, Qt.AlignCenter)
        grid.addWidget(_hdr("Notch filter"),     0, C_NT_EN, 1, 3, Qt.AlignCenter)

        # Row 1: column sub-headers
        grid.addWidget(_hdr("Channel", Qt.AlignLeft), 1, C_CHAN)
        # Enable columns: no text (the super-header names the group)
        grid.addWidget(_hdr("Cutoff"), 1, C_HP_CUT)
        grid.addWidget(_hdr("Order"),  1, C_HP_ORD)
        grid.addWidget(_hdr("Cutoff"), 1, C_LP_CUT)
        grid.addWidget(_hdr("Order"),  1, C_LP_ORD)
        grid.addWidget(_hdr("Cutoff"), 1, C_NT_CUT)
        grid.addWidget(_hdr("Order"),  1, C_NT_ORD)

        # Row 2: "Apply to all channels" — column-wise enable toggles
        apply_row_label = QLabel("Apply to all channels")
        grid.addWidget(apply_row_label, 2, C_CHAN, Qt.AlignLeft | Qt.AlignVCenter)

        self._col_hp    = QCheckBox()
        self._col_lp    = QCheckBox()
        self._col_notch = QCheckBox()

        grid.addWidget(self._col_hp,    2, C_HP_EN, Qt.AlignCenter)
        grid.addWidget(self._col_lp,    2, C_LP_EN, Qt.AlignCenter)
        grid.addWidget(self._col_notch, 2, C_NT_EN, Qt.AlignCenter)

        # Per-channel widget lists
        self._hp_enabled    = []
        self._hp_cutoff     = []
        self._hp_order      = []
        self._lp_enabled    = []
        self._lp_cutoff     = []
        self._lp_order      = []
        self._notch_enabled = []
        self._notch_cutoff  = []
        self._notch_order   = []

        nyquist = sampling_rate / 2.0

        for ch_idx, chaninfo in enumerate(channel_config):
            row = ch_idx + 3  # rows 0-2 are super-header, sub-header, "apply all"

            name_lbl = QLabel(chaninfo["Channel_name"])

            hp_cb  = QCheckBox()
            hp_cut = QDoubleSpinBox()
            hp_cut.setMinimum(0.01)
            hp_cut.setMaximum(nyquist - 0.01)
            hp_cut.setDecimals(2)
            hp_cut.setValue(0.3)
            hp_cut.setSuffix(" Hz")

            hp_ord = QDoubleSpinBox()
            hp_ord.setMinimum(1)
            hp_ord.setMaximum(10)
            hp_ord.setDecimals(0)
            hp_ord.setValue(4)

            lp_cb  = QCheckBox()
            lp_cut = QDoubleSpinBox()
            lp_cut.setMinimum(0.01)
            lp_cut.setMaximum(nyquist - 0.01)
            lp_cut.setDecimals(2)
            lp_cut.setValue(35.0)
            lp_cut.setSuffix(" Hz")

            lp_ord = QDoubleSpinBox()
            lp_ord.setMinimum(1)
            lp_ord.setMaximum(10)
            lp_ord.setDecimals(0)
            lp_ord.setValue(4)

            nt_cb  = QCheckBox()
            nt_cut = QDoubleSpinBox()
            nt_cut.setMinimum(0.01)
            nt_cut.setMaximum(nyquist - 0.01)
            nt_cut.setDecimals(2)
            nt_cut.setValue(50.0)
            nt_cut.setSuffix(" Hz")

            nt_ord = QDoubleSpinBox()
            nt_ord.setMinimum(1)
            nt_ord.setMaximum(10)
            nt_ord.setDecimals(0)
            nt_ord.setValue(4)

            # Propagate changes to all channels when checkbox is ticked
            hp_cb.stateChanged.connect( lambda _, i=ch_idx: self._propagate(i, "hp_enabled"))
            hp_cut.valueChanged.connect(lambda _, i=ch_idx: self._propagate(i, "hp_cutoff"))
            hp_ord.valueChanged.connect(lambda _, i=ch_idx: self._propagate(i, "hp_order"))
            lp_cb.stateChanged.connect( lambda _, i=ch_idx: self._propagate(i, "lp_enabled"))
            lp_cut.valueChanged.connect(lambda _, i=ch_idx: self._propagate(i, "lp_cutoff"))
            lp_ord.valueChanged.connect(lambda _, i=ch_idx: self._propagate(i, "lp_order"))
            nt_cb.stateChanged.connect( lambda _, i=ch_idx: self._propagate(i, "notch_enabled"))
            nt_cut.valueChanged.connect(lambda _, i=ch_idx: self._propagate(i, "notch_cutoff"))
            nt_ord.valueChanged.connect(lambda _, i=ch_idx: self._propagate(i, "notch_order"))

            grid.addWidget(name_lbl, row, C_CHAN,   Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(hp_cb,    row, C_HP_EN,  Qt.AlignCenter)
            grid.addWidget(hp_cut,   row, C_HP_CUT)
            grid.addWidget(hp_ord,   row, C_HP_ORD)
            grid.addWidget(lp_cb,    row, C_LP_EN,  Qt.AlignCenter)
            grid.addWidget(lp_cut,   row, C_LP_CUT)
            grid.addWidget(lp_ord,   row, C_LP_ORD)
            grid.addWidget(nt_cb,    row, C_NT_EN,  Qt.AlignCenter)
            grid.addWidget(nt_cut,   row, C_NT_CUT)
            grid.addWidget(nt_ord,   row, C_NT_ORD)

            self._hp_enabled.append(hp_cb)
            self._hp_cutoff.append(hp_cut)
            self._hp_order.append(hp_ord)
            self._lp_enabled.append(lp_cb)
            self._lp_cutoff.append(lp_cut)
            self._lp_order.append(lp_ord)
            self._notch_enabled.append(nt_cb)
            self._notch_cutoff.append(nt_cut)
            self._notch_order.append(nt_ord)

        # Push content to the top — sink all spare vertical space into an empty last row
        grid.setRowStretch(len(channel_config) + 3, 1)
        # Push content to the left
        grid.setColumnStretch(LAST_COL + 1, 1)

        # Column-wise "apply to all" toggles
        self._col_hp.stateChanged.connect(   lambda s: self._set_all_column(self._hp_enabled,    s))
        self._col_lp.stateChanged.connect(   lambda s: self._set_all_column(self._lp_enabled,    s))
        self._col_notch.stateChanged.connect(lambda s: self._set_all_column(self._notch_enabled, s))

        # Apply button
        apply_button = QPushButton("Apply")
        apply_button.setFixedWidth(100)
        apply_button.clicked.connect(self._on_apply)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(apply_button)
        layout.addLayout(button_layout)

    def _set_all_column(self, checkbox_list, state):
        checked = bool(state)
        for cb in checkbox_list:
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)

    def _propagate(self, src_idx, prop):
        if not self.apply_all_checkbox.isChecked():
            return
        widget_lists = {
            "hp_enabled":    self._hp_enabled,
            "hp_cutoff":     self._hp_cutoff,
            "hp_order":      self._hp_order,
            "lp_enabled":    self._lp_enabled,
            "lp_cutoff":     self._lp_cutoff,
            "lp_order":      self._lp_order,
            "notch_enabled": self._notch_enabled,
            "notch_cutoff":  self._notch_cutoff,
            "notch_order":   self._notch_order,
        }
        src_widget = widget_lists[prop][src_idx]
        for i, w in enumerate(widget_lists[prop]):
            if i == src_idx:
                continue
            w.blockSignals(True)
            if isinstance(src_widget, QCheckBox):
                w.setChecked(src_widget.isChecked())
            else:
                w.setValue(src_widget.value())
            w.blockSignals(False)

    def _on_apply(self):
        filter_settings = []
        for i in range(len(self._channel_config)):
            filter_settings.append({
                "hp_enabled":    self._hp_enabled[i].isChecked(),
                "hp_cutoff":     self._hp_cutoff[i].value(),
                "hp_order":      int(self._hp_order[i].value()),
                "lp_enabled":    self._lp_enabled[i].isChecked(),
                "lp_cutoff":     self._lp_cutoff[i].value(),
                "lp_order":      int(self._lp_order[i].value()),
                "notch_enabled": self._notch_enabled[i].isChecked(),
                "notch_cutoff":  self._notch_cutoff[i].value(),
                "notch_order":   int(self._notch_order[i].value()),
            })
        apply_filter(self._eeg_data, self._sampling_rate, filter_settings)
        self.filterApplied.emit()
