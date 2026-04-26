import numpy as np
import pyqtgraph as pg
from scipy.signal import cheby2, sosfreqz

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
        self.resize(920, 500)
        self._channel_config = channel_config
        self._sampling_rate = sampling_rate

        layout = QVBoxLayout(self)

        # Info label
        description = QLabel(
            "\u24d8 "
            "High-pass, low-pass, or notch-filter a given EEG channel using a "
            "Chebyshev Type 2 filter. The specified cutoff frequency is the "
            "\u221260\u202fdB stopband edge, not the \u22123\u202fdB point. "
            "Filters affect only the displayed EEG signal, not any power computations. "
            "Click \u223f to plot the magnitude response of a filter."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        # "Apply" checkbox — when checked, changing any parameter on one channel propagates to all
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

        def _vsep():
            sep = QFrame()
            sep.setFrameShape(QFrame.VLine)
            sep.setFrameShadow(QFrame.Plain)
            sep.setFixedWidth(1)
            return sep

        # Column layout: Channel | HP cut/ord/en/plt | sep | LP cut/ord/en/plt | sep | Notch cut/ord/en/plt | vsep | All
        C_CHAN = 0
        C_HP_CUT, C_HP_ORD, C_HP_EN, C_HP_PLT = 1, 2, 3, 4
        C_SEP1 = 5
        C_LP_CUT, C_LP_ORD, C_LP_EN, C_LP_PLT = 6, 7, 8, 9
        C_SEP2 = 10
        C_NT_CUT, C_NT_ORD, C_NT_EN, C_NT_PLT = 11, 12, 13, 14
        C_SEP3 = 15
        C_ALL = 16
        LAST_COL = 16

        # Visual spacing between filter groups
        grid.setColumnMinimumWidth(C_SEP1, 22)
        grid.setColumnMinimumWidth(C_SEP2, 22)
        grid.setColumnMinimumWidth(C_SEP3, 22)

        # Row 0: filter-group super-headers (spanning 4 columns each)
        grid.addWidget(_hdr("High-pass filter"), 0, C_HP_CUT, 1, 4, Qt.AlignCenter)
        grid.addWidget(_hdr("Low-pass filter"),  0, C_LP_CUT, 1, 4, Qt.AlignCenter)
        grid.addWidget(_hdr("Notch filter"),     0, C_NT_CUT, 1, 4, Qt.AlignCenter)
        grid.addWidget(_hdr("Select all\nfilters"), 0, C_ALL, 2, 1, Qt.AlignCenter)

        # Row 1: column sub-headers
        grid.addWidget(_hdr("Channel", Qt.AlignLeft), 1, C_CHAN)
        grid.addWidget(_hdr("Cutoff", Qt.AlignLeft), 1, C_HP_CUT)
        grid.addWidget(_hdr("Order",  Qt.AlignLeft), 1, C_HP_ORD)
        grid.addWidget(_hdr("Cutoff", Qt.AlignLeft), 1, C_LP_CUT)
        grid.addWidget(_hdr("Order",  Qt.AlignLeft), 1, C_LP_ORD)
        grid.addWidget(_hdr("Cutoff", Qt.AlignLeft), 1, C_NT_CUT)
        grid.addWidget(_hdr("Order",  Qt.AlignLeft), 1, C_NT_ORD)

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
            hp_ord.setMaximumWidth(60)

            hp_plt = QPushButton("\u223f")
            hp_plt.setFixedSize(20, 20)
            hp_plt.setToolTip("Plot high-pass frequency response")

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
            lp_ord.setMaximumWidth(60)

            lp_plt = QPushButton("\u223f")
            lp_plt.setFixedSize(20, 20)
            lp_plt.setToolTip("Plot low-pass frequency response")

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
            nt_ord.setMaximumWidth(60)

            nt_plt = QPushButton("\u223f")
            nt_plt.setFixedSize(20, 20)
            nt_plt.setToolTip("Plot notch frequency response")

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

            hp_plt.clicked.connect(lambda _, i=ch_idx: self._plot_filter_response("hp", i))
            lp_plt.clicked.connect(lambda _, i=ch_idx: self._plot_filter_response("lp", i))
            nt_plt.clicked.connect(lambda _, i=ch_idx: self._plot_filter_response("notch", i))

            grid.addWidget(name_lbl, row, C_CHAN,   Qt.AlignLeft | Qt.AlignVCenter)
            grid.addWidget(hp_cut,   row, C_HP_CUT)
            grid.addWidget(hp_ord,   row, C_HP_ORD)
            grid.addWidget(hp_cb,    row, C_HP_EN,  Qt.AlignCenter)
            grid.addWidget(hp_plt,   row, C_HP_PLT, Qt.AlignCenter)
            grid.addWidget(lp_cut,   row, C_LP_CUT)
            grid.addWidget(lp_ord,   row, C_LP_ORD)
            grid.addWidget(lp_cb,    row, C_LP_EN,  Qt.AlignCenter)
            grid.addWidget(lp_plt,   row, C_LP_PLT, Qt.AlignCenter)
            grid.addWidget(nt_cut,   row, C_NT_CUT)
            grid.addWidget(nt_ord,   row, C_NT_ORD)
            grid.addWidget(nt_cb,    row, C_NT_EN,  Qt.AlignCenter)
            grid.addWidget(nt_plt,   row, C_NT_PLT, Qt.AlignCenter)
            grid.addWidget(_vsep(),  row, C_SEP3,   Qt.AlignCenter)
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

    def _plot_filter_response(self, filter_type, ch_idx):
        fs = self._sampling_rate
        nyquist = fs / 2.0
        ch_name = self._channel_config[ch_idx]["Channel_name"]

        if filter_type == "hp":
            cutoff = self._hp_cutoff[ch_idx].value()
            order  = int(self._hp_order[ch_idx].value())
            if not (0 < cutoff < nyquist):
                return
            sos = cheby2(order, 60, cutoff, btype="highpass", fs=fs, output="sos")
            title = f"High-pass  |  {ch_name}  |  Cutoff: {cutoff} Hz, Order: {order}"
            vlines = [cutoff]
        elif filter_type == "lp":
            cutoff = self._lp_cutoff[ch_idx].value()
            order  = int(self._lp_order[ch_idx].value())
            if not (0 < cutoff < nyquist):
                return
            sos = cheby2(order, 60, cutoff, btype="lowpass", fs=fs, output="sos")
            title = f"Low-pass  |  {ch_name}  |  Cutoff: {cutoff} Hz, Order: {order}"
            vlines = [cutoff]
        else:  # notch
            cutoff = self._notch_cutoff[ch_idx].value()
            order  = int(self._notch_order[ch_idx].value())
            low, high = cutoff - 1.0, cutoff + 1.0
            if not (low > 0 and high < nyquist):
                return
            sos = cheby2(order, 60, [low, high], btype="bandstop", fs=fs, output="sos")
            title = f"Notch  |  {ch_name}  |  Cutoff: {cutoff} Hz, Order: {order}"
            vlines = [low, high]

        w, h = sosfreqz(sos, worN=8192, fs=fs)

        # sosfiltfilt applies the filter forward then backward, which squares the magnitude
        mag     = np.abs(h) ** 2
        mag_db  = 20.0 * np.log10(np.maximum(mag, 1e-12))
        mag_pct = mag * 100.0

        ref_3db_pct  = 100.0 * 10 ** (-3.0  / 20.0)   # ≈ 70.8 %
        ref_60db_pct = 100.0 * 10 ** (-60.0 / 20.0)   # = 0.1 %

        dash = Qt.PenStyle.DashLine
        dot  = Qt.PenStyle.DotLine
        orange = (255, 165, 0)

        win = pg.GraphicsLayoutWidget()
        win.setBackground("w")

        p1 = win.addPlot(title=title)
        p1.setLabel("left", "Magnitude (dB)")
        p1.setLabel("bottom", "Frequency (Hz)")
        p1.setXRange(0, nyquist, padding=0)
        p1.showGrid(x=True, y=True, alpha=0.3)
        p1.plot(w, mag_db, pen=pg.mkPen("k", width=1.5))
        for vl in vlines:
            p1.addItem(pg.InfiniteLine(pos=vl, angle=90, pen=pg.mkPen("r", width=1, style=dash)))
        p1.addItem(pg.InfiniteLine(pos=-3,  angle=0, pen=pg.mkPen(orange, width=1, style=dot),
                                   label="\u22123 dB", labelOpts={"color": orange, "position": 0.95}))
        p1.addItem(pg.InfiniteLine(pos=-60, angle=0, pen=pg.mkPen("r", width=1, style=dot),
                                   label="\u221260 dB", labelOpts={"color": "r", "position": 0.95}))

        win.nextRow()

        p2 = win.addPlot()
        p2.setLabel("left", "Magnitude (%)")
        p2.setLabel("bottom", "Frequency (Hz)")
        p2.setXRange(0, nyquist, padding=0)
        p2.showGrid(x=True, y=True, alpha=0.3)
        p2.plot(w, mag_pct, pen=pg.mkPen("k", width=1.5))
        for vl in vlines:
            p2.addItem(pg.InfiniteLine(pos=vl, angle=90, pen=pg.mkPen("r", width=1, style=dash)))
        p2.addItem(pg.InfiniteLine(pos=ref_3db_pct,  angle=0, pen=pg.mkPen(orange, width=1, style=dot),
                                   label=f"{ref_3db_pct:.1f}% (\u22123 dB)",
                                   labelOpts={"color": orange, "position": 0.95}))
        p2.addItem(pg.InfiniteLine(pos=ref_60db_pct, angle=0, pen=pg.mkPen("r", width=1, style=dot),
                                   label=f"{ref_60db_pct:.2f}% (\u221260 dB)",
                                   labelOpts={"color": "r", "position": 0.95}))

        dlg = QDialog(self)
        dlg.setWindowTitle("Filter frequency response")
        dlg.resize(700, 520)
        v = QVBoxLayout(dlg)
        v.setContentsMargins(4, 4, 4, 4)
        v.addWidget(win)
        dlg.show()

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
