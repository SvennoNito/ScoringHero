import os
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import (
    QFileDialog, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QGroupBox, QCheckBox, QPushButton, QRadioButton, QButtonGroup, QLabel, QLineEdit,
)
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import tempfile
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import io


class _ReportOptionsDialog(QDialog):
    def __init__(self, ui):
        super().__init__(ui)
        self._ui = ui
        self._preview_files = []
        self.setWindowTitle("Sleep Report Options")
        self.setMinimumWidth(320)

        layout = QVBoxLayout()

        general_group = QGroupBox("General")
        general_layout = QHBoxLayout()
        general_layout.addWidget(QLabel("Name:"))
        self.le_filename = QLineEdit()
        self.le_filename.setText(os.path.basename(ui.filename) if ui.filename else "")
        general_layout.addWidget(self.le_filename)
        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        plots_group = QGroupBox("Plots")
        plots_layout = QVBoxLayout()

        self.cb_hypnogram = QCheckBox("Hypnogram")
        self.cb_hypnogram.setChecked(True)
        plots_layout.addWidget(self.cb_hypnogram)

        # Hypnogram style sub-options (indented)
        hyp_sub = QVBoxLayout()
        hyp_sub.setContentsMargins(20, 0, 0, 0)

        self.cb_hyp_line = QCheckBox("Show stage line")
        self.cb_hyp_line.setChecked(False)
        hyp_sub.addWidget(self.cb_hyp_line)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color areas:"))
        self.rb_colors_all = QRadioButton("All stages")
        self.rb_colors_all.setChecked(True)
        self.rb_colors_rem = QRadioButton("REM only")
        self.rb_colors_none = QRadioButton("None")
        self._hyp_color_group = QButtonGroup(self)
        self._hyp_color_group.addButton(self.rb_colors_all)
        self._hyp_color_group.addButton(self.rb_colors_rem)
        self._hyp_color_group.addButton(self.rb_colors_none)
        color_row.addWidget(self.rb_colors_all)
        color_row.addWidget(self.rb_colors_rem)
        color_row.addWidget(self.rb_colors_none)
        hyp_sub.addLayout(color_row)

        plots_layout.addLayout(hyp_sub)

        self._hyp_style_widgets = [
            self.cb_hyp_line, self.rb_colors_all, self.rb_colors_rem, self.rb_colors_none,
        ]
        self.cb_hypnogram.toggled.connect(
            lambda checked: [w.setEnabled(checked) for w in self._hyp_style_widgets]
        )

        self.cb_spectrogram = QCheckBox("Spectrogram")
        self.cb_spectrogram.setChecked(True)
        plots_layout.addWidget(self.cb_spectrogram)

        plots_group.setLayout(plots_layout)
        layout.addWidget(plots_group)

        stats_group = QGroupBox("Sleep Statistics")
        stats_layout = QVBoxLayout()
        self.cb_sleep_stats = QCheckBox("Total Sleep Time, Recording Time, Efficiency")
        self.cb_sleep_stats.setChecked(True)
        self.cb_stage_distribution = QCheckBox("Sleep Stage Distribution")
        self.cb_stage_distribution.setChecked(True)
        self.cb_latencies = QCheckBox("Latencies")
        self.cb_latencies.setChecked(True)
        self.cb_awakenings = QCheckBox("Awakenings (N2/N3/REM → Wake)")
        self.cb_awakenings.setChecked(True)
        self.cb_arousals = QCheckBox("Arousals (N2/N3/REM → N1)")
        self.cb_arousals.setChecked(True)
        stats_layout.addWidget(self.cb_sleep_stats)
        stats_layout.addWidget(self.cb_stage_distribution)
        stats_layout.addWidget(self.cb_latencies)
        stats_layout.addWidget(self.cb_awakenings)
        stats_layout.addWidget(self.cb_arousals)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        btn_layout = QHBoxLayout()
        btn_preview = QPushButton("Preview")
        btn_preview.clicked.connect(self._show_preview)
        btn_ok = QPushButton("Generate Report")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_preview)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_options(self):
        if self.rb_colors_rem.isChecked():
            hyp_colors = "rem"
        elif self.rb_colors_none.isChecked():
            hyp_colors = "none"
        else:
            hyp_colors = "all"
        return {
            "filename": self.le_filename.text().strip(),
            "hypnogram": self.cb_hypnogram.isChecked(),
            "hyp_line": self.cb_hyp_line.isChecked(),
            "hyp_colors": hyp_colors,
            "spectrogram": self.cb_spectrogram.isChecked(),
            "sleep_stats": self.cb_sleep_stats.isChecked(),
            "stage_distribution": self.cb_stage_distribution.isChecked(),
            "latencies": self.cb_latencies.isChecked(),
            "awakenings": self.cb_awakenings.isChecked(),
            "arousals": self.cb_arousals.isChecked(),
        }

    def _show_preview(self):
        try:
            options = self.get_options()
            ui = self._ui
            hypnogram_img = _create_hypnogram(ui, options) if options["hypnogram"] else None
            spectrogram_img = _create_whole_night_spectrogram(ui) if options["spectrogram"] else None
            any_stats = options["sleep_stats"] or options["stage_distribution"] or options["latencies"] or options["awakenings"] or options["arousals"]
            stats_text = _calculate_sleep_statistics(ui, options) if any_stats else None
            report_filename = options["filename"] or None

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            self._preview_files.append(tmp.name)
            _create_pdf_report(tmp.name, hypnogram_img, spectrogram_img, stats_text, report_filename)
            QDesktopServices.openUrl(QUrl.fromLocalFile(tmp.name))
        except Exception as e:
            QMessageBox.critical(self, "Preview Error", f"Failed to generate preview:\n{str(e)}")

    def closeEvent(self, event):
        for path in self._preview_files:
            try:
                os.unlink(path)
            except Exception:
                pass
        super().closeEvent(event)


def export_sleep_report(ui):
    """Export a sleep report as PDF with hypnogram, spectrogram, and statistics."""

    if not ui.stages or all(stage.get("digit") is None for stage in ui.stages):
        QMessageBox.warning(ui, "No Scoring", "Please score some sleep stages first.")
        return

    dialog = _ReportOptionsDialog(ui)
    if dialog.exec() != QDialog.Accepted:
        return
    options = dialog.get_options()

    if ui.filename:
        initial_path = ui.filename + ".pdf"
    else:
        initial_path = os.path.join(
            os.path.expanduser("~"),
            f"sleep_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        )
    filepath, _ = QFileDialog.getSaveFileName(
        ui,
        "Export Sleep Report",
        initial_path,
        "PDF Files (*.pdf)",
    )

    if not filepath:
        return

    try:
        hypnogram_img = _create_hypnogram(ui, options) if options["hypnogram"] else None
        spectrogram_img = _create_whole_night_spectrogram(ui) if options["spectrogram"] else None

        any_stats = options["sleep_stats"] or options["stage_distribution"] or options["latencies"] or options["awakenings"] or options["arousals"]
        stats_text = _calculate_sleep_statistics(ui, options) if any_stats else None

        report_filename = os.path.basename(ui.filename) if options["filename"] else None
        _create_pdf_report(filepath, hypnogram_img, spectrogram_img, stats_text, report_filename)
        QMessageBox.information(ui, "Success", f"Sleep report saved to:\n{filepath}")
    except Exception as e:
        QMessageBox.critical(ui, "Error", f"Failed to generate report:\n{str(e)}")


_REPORT_FIG_SIZE = (12, 2.5)
_REPORT_DPI = 100
_PLOT_LEFT = 0.10
_PLOT_RIGHT = 0.87
_PLOT_BOTTOM = 0.22
_PLOT_TOP = 0.96
_CBAR_WIDTH = 0.025


def _create_hypnogram(ui, options):
    stages = np.array([stage["digit"] for stage in ui.stages])
    times = np.arange(0, ui.numepo) * ui.config[0]["Epoch_length_s"] / 3600
    epoch_length = ui.config[0]["Epoch_length_s"] / 3600

    stage_colors = {
        1: "#8bbf56",
        0: "#dc5050",
        -1: "#aabcce",
        -2: "#405c79",
        -3: "#0b1c2c",
    }
    stage_y_positions = {1: 4, 0: 3, -1: 2, -2: 1, -3: 0}

    hyp_colors = options.get("hyp_colors", "all")
    show_line = options.get("hyp_line", True)

    fig, ax = plt.subplots(figsize=_REPORT_FIG_SIZE, dpi=_REPORT_DPI)

    for i, stage_value in enumerate(stages):
        if stage_value is None:
            continue
        if hyp_colors == "none":
            continue
        if hyp_colors == "rem" and stage_value != 0:
            continue
        color = stage_colors.get(stage_value, "#cccccc")
        y_pos = stage_y_positions.get(stage_value, 2)
        ax.barh(y_pos, epoch_length, left=times[i], height=0.7, color=color, edgecolor="none")

    if show_line:
        line_x, line_y = [], []
        for i, stage_value in enumerate(stages):
            if stage_value is not None:
                line_x.append(times[i] + epoch_length / 2)
                line_y.append(stage_y_positions[stage_value])
        if line_x:
            ax.plot(line_x, line_y, color="black", linewidth=1.5, zorder=5)

    ax.set_ylim(-0.5, 4.5)
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_yticklabels(["N3", "N2", "N1", "REM", "Wake"], fontsize=12)

    total_hours = ui.numepo * ui.config[0]["Epoch_length_s"] / 3600
    ax.set_xlim(0, total_hours)
    ax.set_xlabel("Time (0h = lights off)", fontsize=11)
    ax.set_xticks(range(int(total_hours) + 1))
    ax.set_xticklabels([f"{h}h" for h in range(int(total_hours) + 1)], fontsize=11)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    fig.subplots_adjust(left=_PLOT_LEFT, right=_PLOT_RIGHT, bottom=_PLOT_BOTTOM, top=_PLOT_TOP)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=_REPORT_DPI)
    buf.seek(0)
    img = Image.open(buf)
    img.load()
    buf.close()
    plt.close(fig)
    return img


def _create_whole_night_spectrogram(ui):
    colormap_path = os.path.join(ui.app_path, "spectral.txt")
    if not os.path.exists(colormap_path):
        raise FileNotFoundError(f"spectral.txt not found at {colormap_path}")

    rgb = np.loadtxt(colormap_path)
    cmap = LinearSegmentedColormap.from_list("spectral", rgb)

    power = np.log10(np.maximum(ui.power, 1e-30))
    freqs = ui.freqs
    power = np.clip(power, -1, 3)

    fig = plt.figure(figsize=_REPORT_FIG_SIZE, dpi=_REPORT_DPI)
    ax_w = _PLOT_RIGHT - _PLOT_LEFT
    ax_h = _PLOT_TOP - _PLOT_BOTTOM
    ax = fig.add_axes([_PLOT_LEFT, _PLOT_BOTTOM, ax_w, ax_h])
    cbar_ax = fig.add_axes([_PLOT_RIGHT + 0.015, _PLOT_BOTTOM, _CBAR_WIDTH, ax_h])

    n_epochs = ui.numepo
    times = np.arange(n_epochs) * ui.config[0]["Epoch_length_s"] / 3600
    im = ax.pcolormesh(times, freqs, power.T, cmap=cmap, shading="auto", vmin=-1, vmax=3)

    ax.set_xlabel("Time (0h = lights off)", fontsize=11)
    ax.set_ylabel("Frequency (Hz)", fontsize=11)
    ax.set_ylim(1, 30)

    total_hours = n_epochs * ui.config[0]["Epoch_length_s"] / 3600
    ax.set_xticks(range(int(total_hours) + 1))
    ax.set_xticklabels([f"{h}h" for h in range(int(total_hours) + 1)], fontsize=11)
    ax.tick_params(axis="y", labelsize=11)

    cbar = plt.colorbar(im, cax=cbar_ax)
    cbar.set_label("Power (dB)", fontsize=10)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=_REPORT_DPI)
    buf.seek(0)
    img = Image.open(buf)
    img.load()
    buf.close()
    plt.close(fig)
    return img


def _calculate_sleep_statistics(ui, options):
    stages = np.array([stage["digit"] for stage in ui.stages], dtype=object)
    epoch_length_s = ui.config[0]["Epoch_length_s"]
    epoch_length_min = epoch_length_s / 60

    scored_mask = np.array([s is not None for s in stages])
    scored_epochs = np.sum(scored_mask)

    wake_epochs = np.sum(stages == 1)
    n1_epochs = np.sum(stages == -1)
    n2_epochs = np.sum(stages == -2)
    n3_epochs = np.sum(stages == -3)
    rem_epochs = np.sum(stages == 0)
    sleep_epochs = scored_epochs - wake_epochs

    tst_min = sleep_epochs * epoch_length_min
    trt_min = scored_epochs * epoch_length_min
    sleep_efficiency = (tst_min / trt_min * 100) if trt_min > 0 else 0

    n1_min = n1_epochs * epoch_length_min
    n2_min = n2_epochs * epoch_length_min
    n3_min = n3_epochs * epoch_length_min
    rem_min = rem_epochs * epoch_length_min

    lines = []

    if options["sleep_stats"]:
        lines += [
            "SLEEP STATISTICS",
            "-" * 50,
            f"Total Sleep Time (TST):        {tst_min:.1f} min ({tst_min/60:.1f} h)",
            f"Total Recording Time (TRT):    {trt_min:.1f} min ({trt_min/60:.1f} h)",
            f"Sleep Efficiency:              {sleep_efficiency:.1f}%",
        ]

    if options["stage_distribution"]:
        wake_pct = (wake_epochs / scored_epochs * 100) if scored_epochs > 0 else 0
        n1_pct = (n1_epochs / scored_epochs * 100) if scored_epochs > 0 else 0
        n2_pct = (n2_epochs / scored_epochs * 100) if scored_epochs > 0 else 0
        n3_pct = (n3_epochs / scored_epochs * 100) if scored_epochs > 0 else 0
        rem_pct = (rem_epochs / scored_epochs * 100) if scored_epochs > 0 else 0

        wake_h = wake_epochs * epoch_length_min / 60
        n1_h = n1_min / 60
        n2_h = n2_min / 60
        n3_h = n3_min / 60
        rem_h = rem_min / 60

        if lines:
            lines.append("")
        lines += [
            "SLEEP STAGE DISTRIBUTION",
            "-" * 50,
            f"{'Wake:':<31}{wake_epochs * epoch_length_min:.1f} min ({wake_h:.1f} h) - {wake_pct:.1f}%",
            f"{'REM:':<31}{rem_min:.1f} min ({rem_h:.1f} h) - {rem_pct:.1f}%",
            f"{'N1:':<31}{n1_min:.1f} min ({n1_h:.1f} h) - {n1_pct:.1f}%",
            f"{'N2:':<31}{n2_min:.1f} min ({n2_h:.1f} h) - {n2_pct:.1f}%",
            f"{'N3:':<31}{n3_min:.1f} min ({n3_h:.1f} h) - {n3_pct:.1f}%",
        ]

    if options["latencies"]:
        n2_onset_idx = np.where(stages == -2)[0]
        n2_latency_min = n2_onset_idx[0] * epoch_length_min if len(n2_onset_idx) > 0 else None

        n3_onset_idx = np.where(stages == -3)[0]
        n3_latency_min = n3_onset_idx[0] * epoch_length_min if len(n3_onset_idx) > 0 else None

        rem_onset_idx = np.where(stages == 0)[0]
        rem_latency_min = rem_onset_idx[0] * epoch_length_min if len(rem_onset_idx) > 0 else None

        if lines:
            lines.append("")
        lines += [
            "LATENCIES",
            "-" * 50,
            f"N2 latency:                    {n2_latency_min:.1f} min" if n2_latency_min is not None else "N2 latency:                    N/A",
            f"N3 latency:                    {n3_latency_min:.1f} min" if n3_latency_min is not None else "N3 latency:                    N/A",
            f"REM latency:                   {rem_latency_min:.1f} min" if rem_latency_min is not None else "REM latency:                   N/A",
        ]

    if options["awakenings"] or options["arousals"]:
        sleep_set = {-3, -2, 0}
        scored_list = [s for s in stages.tolist() if s is not None]
        n = len(scored_list)
        sleep_positions = [i for i, s in enumerate(scored_list) if s in sleep_set]
        last_sleep_pos = sleep_positions[-1] if sleep_positions else None

    if options["awakenings"]:
        n3_to_wake = n2_to_wake = rem_to_wake = 0
        awakening_durations = []

        if last_sleep_pos is not None:
            i = 1
            while i < n:
                prev = scored_list[i - 1]
                curr = scored_list[i]
                if curr == 1 and prev in sleep_set and i < last_sleep_pos:
                    if prev == -3:
                        n3_to_wake += 1
                    elif prev == -2:
                        n2_to_wake += 1
                    elif prev == 0:
                        rem_to_wake += 1
                    j = i
                    while j < n and scored_list[j] == 1:
                        j += 1
                    awakening_durations.append((j - i) * epoch_length_min)
                    i = j
                else:
                    i += 1

        total_awakenings = n3_to_wake + n2_to_wake + rem_to_wake
        avg_awk = f"{np.mean(awakening_durations):.1f} min" if awakening_durations else "N/A"

        if lines:
            lines.append("")
        lines += [
            "AWAKENINGS",
            "-" * 50,
            f"{'N3 -> Wake:':<31}{n3_to_wake}",
            f"{'N2 -> Wake:':<31}{n2_to_wake}",
            f"{'REM -> Wake:':<31}{rem_to_wake}",
            f"{'Total:':<31}{total_awakenings}",
            f"{'Avg. duration:':<31}{avg_awk}",
        ]

    if options["arousals"]:
        if last_sleep_pos is not None:
            n3_to_n1 = sum(1 for i in range(1, n) if scored_list[i] == -1 and scored_list[i - 1] == -3)
            n2_to_n1 = sum(1 for i in range(1, n) if scored_list[i] == -1 and scored_list[i - 1] == -2)
            rem_to_n1 = sum(1 for i in range(1, n) if scored_list[i] == -1 and scored_list[i - 1] == 0)
        else:
            n3_to_n1 = n2_to_n1 = rem_to_n1 = 0

        total_arousals = n3_to_n1 + n2_to_n1 + rem_to_n1

        if lines:
            lines.append("")
        lines += [
            "AROUSALS",
            "-" * 50,
            f"{'N3 -> N1:':<31}{n3_to_n1}",
            f"{'N2 -> N1:':<31}{n2_to_n1}",
            f"{'REM -> N1:':<31}{rem_to_n1}",
            f"{'Total:':<31}{total_arousals}",
        ]

    return "\n".join(lines)


def _create_pdf_report(filepath, hypnogram_img, spectrogram_img, stats_text, report_filename=None):
    page_width, page_height = letter
    c = canvas.Canvas(filepath, pagesize=letter)

    left_x = 0.5 * inch
    plot_width = page_width - 2 * left_x  # 7.5 inch for letter with 0.5 inch margins
    plot_height = plot_width * _REPORT_FIG_SIZE[1] / _REPORT_FIG_SIZE[0]

    tmp_files = []
    hypno_path = spec_path = None

    try:
        if hypnogram_img is not None:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                hypnogram_img.save(f.name)
                hypno_path = f.name
                tmp_files.append(f.name)

        if spectrogram_img is not None:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                spectrogram_img.save(f.name)
                spec_path = f.name
                tmp_files.append(f.name)

        c.setFont("Helvetica-Bold", 16)
        c.drawString(left_x, page_height - 0.55 * inch, "Sleep Report")

        current_y = page_height - 0.75 * inch

        if report_filename:
            c.setFont("Helvetica", 10)
            c.drawString(left_x, current_y, report_filename)
            current_y -= 0.25 * inch

        current_y -= 0.1 * inch

        if hypno_path:
            hypno_y = current_y - plot_height
            c.drawImage(hypno_path, left_x, hypno_y, width=plot_width, height=plot_height)
            current_y = hypno_y - 0.15 * inch

        if spec_path:
            spec_y = current_y - plot_height
            c.drawImage(spec_path, left_x, spec_y, width=plot_width, height=plot_height)
            current_y = spec_y - 0.15 * inch

        if stats_text:
            c.setFont("Courier", 9)
            text_y = current_y - 0.25 * inch
            for line in stats_text.split("\n"):
                if text_y < 0.5 * inch:
                    break
                c.drawString(left_x, text_y, line)
                text_y -= 0.12 * inch

        c.save()
    finally:
        for path in tmp_files:
            try:
                os.unlink(path)
            except Exception:
                pass
