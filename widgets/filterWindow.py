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
    QFrame,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

class FilterWindow(QDialog):
    filterApplied = Signal(list)

    def __init__(self, channel_config, sampling_rate, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter")
        self.resize(820, 500)
        self._channel_config = channel_config
        self._sampling_rate = sampling_rate

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

        # "Apply" checkbox — when checked, changing any parameter on one channel propagates to all
        self.apply_all_checkbox = QCheckBox("Apply")
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

        def _vsep():
            sep = QFrame()
            sep.setFrameShape(QFrame.VLine)
            sep.setFrameShadow(QFrame.Sunken)
            return sep

        # Column layout: Channel | HP cut/ord/en | sep | LP cut/ord/en | sep | Notch cut/ord/en | vsep | All
        C_CHAN = 0
        C_HP_CUT, C_HP_ORD, C_HP_EN = 1, 2, 3
        C_SEP1 = 4
        C_LP_CUT, C_LP_ORD, C_LP_EN = 5, 6, 7
        C_SEP2 = 8
        C_NT_CUT, C_NT_ORD, C_NT_EN = 9, 10, 11
        C_SEP3 = 12
        C_ALL = 13
        LAST_COL = 13

        # Visual spacing between filter groups
        grid.setColumnMinimumWidth(C_SEP1, 18)
        grid.setColumnMinimumWidth(C_SEP2, 18)
        grid.setColumnMinimumWidth(C_SEP3, 18)

        # Row 0: filter-group super-headers (spanning 3 columns each)
        grid.addWidget(_hdr("High-pass filter"), 0, C_HP_CUT, 1, 3, Qt.AlignCenter)
        grid.addWidget(_hdr("Low-pass filter"),  0, C_LP_CUT, 1, 3, Qt.AlignCenter)
        grid.addWidget(_hdr("Notch filter"),     0, C_NT_CUT, 1, 3, Qt.AlignCenter)
        grid.addWidget(_hdr("All"),              0, C_ALL,    1, 1, Qt.AlignCenter)


        # Row 1: column sub-headers
        grid.addWidget(_hdr("Channel", Qt.AlignLeft), 1, C_CHAN)
        grid.addWidget(_hdr("Cutoff"), 1, C_HP_CUT)
        grid.addWidget(_hdr("Order"),  1, C_HP_ORD)
        grid.addWidget(_hdr("Cutoff"), 1, C_LP_CUT)
        grid.addWidget(_hdr("Order"),  1, C_LP_ORD)
        grid.addWidget(_hdr("Cutoff"), 1, C_NT_CUT)
        grid.addWidget(_hdr("Order"),  1, C_NT_ORD)

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
        self._all_enabled   = []

        nyquist = sampling_rate / 2.0

        for ch_idx, chaninfo in enumerate(channel_config):
            row = ch_idx + 2  # rows 0-1 are super-header and sub-header

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
            lp_cut.setValue(50.0)
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

            all_cb = QCheckBox()

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
            all_cb.stateChanged.connect(lambda state, i=ch_idx: self._set_all_row(i, state))

            grid.addWidget(name_lbl, row, C_CHAN,   Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(hp_cut,   row, C_HP_CUT)
            grid.addWidget(hp_ord,   row, C_HP_ORD)
            grid.addWidget(hp_cb,    row, C_HP_EN,  Qt.AlignCenter)
            grid.addWidget(lp_cut,   row, C_LP_CUT)
            grid.addWidget(lp_ord,   row, C_LP_ORD)
            grid.addWidget(lp_cb,    row, C_LP_EN,  Qt.AlignCenter)
            grid.addWidget(nt_cut,   row, C_NT_CUT)
            grid.addWidget(nt_ord,   row, C_NT_ORD)
            grid.addWidget(nt_cb,    row, C_NT_EN,  Qt.AlignCenter)
            grid.addWidget(_vsep(),  row, C_SEP3,  Qt.AlignHCenter)
            grid.addWidget(all_cb,   row, C_ALL,    Qt.AlignCenter)

            self._hp_enabled.append(hp_cb)
            self._hp_cutoff.append(hp_cut)
            self._hp_order.append(hp_ord)
            self._lp_enabled.append(lp_cb)
            self._lp_cutoff.append(lp_cut)
            self._lp_order.append(lp_ord)
            self._notch_enabled.append(nt_cb)
            self._notch_cutoff.append(nt_cut)
            self._notch_order.append(nt_ord)
            self._all_enabled.append(all_cb)

        # Push content to the top — sink all spare vertical space into an empty last row
        grid.setRowStretch(len(channel_config) + 2, 1)
        # Push content to the left
        grid.setColumnStretch(LAST_COL + 1, 1)

        # Apply button
        apply_button = QPushButton("Apply")
        apply_button.setFixedWidth(100)
        apply_button.clicked.connect(self._on_apply)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(apply_button)
        layout.addLayout(button_layout)

    def load_settings(self, channel_config):
        for i, chaninfo in enumerate(channel_config):
            widgets = [
                self._hp_cutoff[i], self._hp_order[i], self._hp_enabled[i],
                self._lp_cutoff[i], self._lp_order[i], self._lp_enabled[i],
                self._notch_cutoff[i], self._notch_order[i], self._notch_enabled[i],
            ]
            for w in widgets:
                w.blockSignals(True)
            self._hp_cutoff[i].setValue(chaninfo.get("Filter_hp_cutoff", 0.3))
            self._hp_order[i].setValue(chaninfo.get("Filter_hp_order", 4))
            self._hp_enabled[i].setChecked(chaninfo.get("Filter_hp_enabled", False))
            self._lp_cutoff[i].setValue(chaninfo.get("Filter_lp_cutoff", 50.0))
            self._lp_order[i].setValue(chaninfo.get("Filter_lp_order", 4))
            self._lp_enabled[i].setChecked(chaninfo.get("Filter_lp_enabled", False))
            self._notch_cutoff[i].setValue(chaninfo.get("Filter_notch_cutoff", 50.0))
            self._notch_order[i].setValue(chaninfo.get("Filter_notch_order", 4))
            self._notch_enabled[i].setChecked(chaninfo.get("Filter_notch_enabled", False))
            for w in widgets:
                w.blockSignals(False)

    def _set_all_row(self, ch_idx, state):
        checked = bool(state)
        targets = (
            [self._hp_enabled, self._lp_enabled, self._notch_enabled]
            if self.apply_all_checkbox.isChecked()
            else None
        )
        for filter_list in [self._hp_enabled, self._lp_enabled, self._notch_enabled]:
            rows = range(len(filter_list)) if targets is not None else [ch_idx]
            for i in rows:
                filter_list[i].blockSignals(True)
                filter_list[i].setChecked(checked)
                filter_list[i].blockSignals(False)

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
        self.filterApplied.emit(filter_settings)
