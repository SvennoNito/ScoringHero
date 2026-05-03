import os
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import tempfile
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import io


def export_sleep_report(ui):
    """Export a sleep report as PDF with hypnogram, spectrogram, and statistics."""

    # Check if stages exist
    if not ui.stages or all(stage.get("digit") is None for stage in ui.stages):
        QMessageBox.warning(ui, "No Scoring", "Please score some sleep stages first.")
        return

    # Get filename
    initial_filename = f"sleep_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath, _ = QFileDialog.getSaveFileName(
        ui,
        "Export Sleep Report",
        os.path.join(os.path.expanduser("~"), initial_filename),
        "PDF Files (*.pdf)",
    )

    if not filepath:
        return

    try:
        # Generate figures
        hypnogram_img = _create_hypnogram(ui)
        spectrogram_img = _create_whole_night_spectrogram(ui)
        stats_text = _calculate_sleep_statistics(ui)

        # Create PDF
        _create_pdf_report(filepath, hypnogram_img, spectrogram_img, stats_text, ui)
        QMessageBox.information(ui, "Success", f"Sleep report saved to:\n{filepath}")
    except Exception as e:
        QMessageBox.critical(ui, "Error", f"Failed to generate report:\n{str(e)}")


def _create_hypnogram(ui):
    """Create a beautiful hypnogram using matplotlib."""
    stages = np.array([stage["digit"] for stage in ui.stages])
    times = np.arange(0, ui.numepo) * ui.config[0]["Epoch_length_s"] / 3600  # hours
    epoch_length = ui.config[0]["Epoch_length_s"] / 3600

    # Stage configuration - Order: Wake, REM, N1, N2, N3 (top to bottom)
    stage_colors = {
        1: "#8bbf56",   # Wake
        0: "#dc5050",   # REM (solid red)
        -1: "#aabcce",  # N1
        -2: "#405c79",  # N2
        -3: "#0b1c2c",  # N3
    }

    stage_y_positions = {
        1: 4,   # Wake
        0: 3,   # REM
        -1: 2,  # N1
        -2: 1,  # N2
        -3: 0,  # N3
    }

    fig, ax = plt.subplots(figsize=(12, 2.5), dpi=100)

    # Draw colored rectangles for each stage
    for i, stage_value in enumerate(stages):
        if stage_value is not None:
            color = stage_colors.get(stage_value, "#cccccc")
            y_pos = stage_y_positions.get(stage_value, 2)
            ax.barh(y_pos, epoch_length, left=times[i], height=0.7, color=color, edgecolor="none")

    # Draw black line tracing the stages
    line_x = []
    line_y = []
    for i, stage_value in enumerate(stages):
        if stage_value is not None:
            line_x.append(times[i] + epoch_length / 2)
            line_y.append(stage_y_positions[stage_value])

    if line_x:
        ax.plot(line_x, line_y, color="black", linewidth=2.5, zorder=5)

    # Set y-axis
    ax.set_ylim(-0.5, 4.5)
    ax.set_yticks([0, 1, 2, 3, 4])
    ax.set_yticklabels(["N3", "N2", "N1", "REM", "Wake"], fontsize=12)

    # Set x-axis
    total_hours = ui.numepo * ui.config[0]["Epoch_length_s"] / 3600
    ax.set_xlim(0, total_hours)
    ax.set_xlabel("Time (0h = lights off)", fontsize=11)
    ax.set_xticks(range(int(total_hours) + 1))
    ax.set_xticklabels([f"{h}h" for h in range(int(total_hours) + 1)], fontsize=11)

    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()

    # Convert to PIL Image
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    buf.seek(0)
    img = Image.open(buf)
    img.load()
    buf.close()
    plt.close(fig)

    return img


def _create_whole_night_spectrogram(ui):
    """Create a whole-night spectrogram using matplotlib and spectral colormap."""
    # Load spectral colormap
    colormap_path = os.path.join(ui.app_path, "spectral.txt")
    if not os.path.exists(colormap_path):
        raise FileNotFoundError(f"spectral.txt not found at {colormap_path}")

    rgb = np.loadtxt(colormap_path)  # (N, 3), 0-1
    cmap = LinearSegmentedColormap.from_list("spectral", rgb)

    # Use cached spectral data
    power = np.log10(np.maximum(ui.power, 1e-30))[:, ui.freqsOI]
    freqs = ui.freqs[ui.freqsOI]

    # Normalize to [-1, 3] range
    power = np.clip(power, -1, 3)

    # Create figure with GridSpec to control colorbar separately
    fig = plt.figure(figsize=(13.5, 2.5), dpi=100)
    gs = fig.add_gridspec(1, 2, width_ratios=[12, 0.4], hspace=0.3, wspace=0.3)
    ax = fig.add_subplot(gs[0, 0])
    cbar_ax = fig.add_subplot(gs[0, 1])

    # Create spectrogram plot
    n_epochs = ui.numepo
    times = np.arange(n_epochs) * ui.config[0]["Epoch_length_s"] / 3600

    im = ax.pcolormesh(times, freqs, power.T, cmap=cmap, shading="auto", vmin=-1, vmax=3)

    ax.set_xlabel("Time (0h = lights off)", fontsize=11)
    ax.set_ylabel("Frequency (Hz)", fontsize=11)

    # Set frequency limit
    freq_max = min(freqs[-1], 50)
    ax.set_ylim(freqs[0], freq_max)

    # Format x-axis with larger ticks
    total_hours = n_epochs * ui.config[0]["Epoch_length_s"] / 3600
    ax.set_xticks(range(int(total_hours) + 1))
    ax.set_xticklabels([f"{h}h" for h in range(int(total_hours) + 1)], fontsize=11)
    ax.tick_params(axis='y', labelsize=11)

    # Add colorbar to separate axis
    cbar = plt.colorbar(im, cax=cbar_ax)
    cbar.set_label("Power (dB)", fontsize=10)

    plt.tight_layout()

    # Convert to PIL Image
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    buf.seek(0)
    img = Image.open(buf)
    img.load()
    buf.close()
    plt.close(fig)

    return img


def _calculate_sleep_statistics(ui):
    """Calculate sleep statistics and return as formatted text."""

    stages = np.array([stage["digit"] for stage in ui.stages], dtype=object)
    epoch_length_s = ui.config[0]["Epoch_length_s"]
    epoch_length_min = epoch_length_s / 60

    # Compute statistics
    total_epochs = len(stages)

    # Create mask for scored epochs (not None)
    scored_mask = np.array([s is not None for s in stages])
    scored_epochs = np.sum(scored_mask)

    wake_epochs = np.sum(stages == 1)
    n1_epochs = np.sum(stages == -1)
    n2_epochs = np.sum(stages == -2)
    n3_epochs = np.sum(stages == -3)
    rem_epochs = np.sum(stages == 0)
    sleep_epochs = scored_epochs - wake_epochs

    # Time calculations
    tst_min = sleep_epochs * epoch_length_min  # Total Sleep Time
    trt_min = scored_epochs * epoch_length_min  # Total Recording Time
    sleep_efficiency = (tst_min / trt_min * 100) if trt_min > 0 else 0

    # Stage times
    n1_min = n1_epochs * epoch_length_min
    n2_min = n2_epochs * epoch_length_min
    n3_min = n3_epochs * epoch_length_min
    rem_min = rem_epochs * epoch_length_min

    # Latencies - separate for N2, N3, and REM
    n2_onset_idx = np.where(stages == -2)[0]
    n2_latency_min = None
    if len(n2_onset_idx) > 0:
        n2_latency_min = n2_onset_idx[0] * epoch_length_min

    n3_onset_idx = np.where(stages == -3)[0]
    n3_latency_min = None
    if len(n3_onset_idx) > 0:
        n3_latency_min = n3_onset_idx[0] * epoch_length_min

    rem_onset_idx = np.where(stages == 0)[0]
    rem_latency_min = None
    if len(rem_onset_idx) > 0:
        rem_latency_min = rem_onset_idx[0] * epoch_length_min

    # Build text report
    lines = [
        "SLEEP STATISTICS",
        "-" * 50,
        f"Total Sleep Time (TST):        {tst_min:.1f} min ({tst_min/60:.1f} h)",
        f"Total Recording Time (TRT):    {trt_min:.1f} min ({trt_min/60:.1f} h)",
        f"Sleep Efficiency:              {sleep_efficiency:.1f}%",
        "",
        "SLEEP STAGE DISTRIBUTION",
        "-" * 50,
    ]

    # Format: xx.x min (x.x h) - x.x%
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

    lines.extend([
        f"Wake:    {wake_epochs * epoch_length_min:6.1f} min ({wake_h:4.1f} h) - {wake_pct:5.1f}%",
        f"REM:     {rem_min:6.1f} min ({rem_h:4.1f} h) - {rem_pct:5.1f}%",
        f"N1:      {n1_min:6.1f} min ({n1_h:4.1f} h) - {n1_pct:5.1f}%",
        f"N2:      {n2_min:6.1f} min ({n2_h:4.1f} h) - {n2_pct:5.1f}%",
        f"N3:      {n3_min:6.1f} min ({n3_h:4.1f} h) - {n3_pct:5.1f}%",
        "",
        "LATENCIES",
        "-" * 50,
    ])

    if n2_latency_min is not None:
        lines.append(f"N2 latency:                    {n2_latency_min:.1f} min")
    else:
        lines.append(f"N2 latency:                    N/A")

    if n3_latency_min is not None:
        lines.append(f"N3 latency:                    {n3_latency_min:.1f} min")
    else:
        lines.append(f"N3 latency:                    N/A")

    if rem_latency_min is not None:
        lines.append(f"REM latency:                   {rem_latency_min:.1f} min")
    else:
        lines.append(f"REM latency:                   N/A")

    return "\n".join(lines)


def _create_pdf_report(filepath, hypnogram_img, spectrogram_img, stats_text, ui):
    """Create a PDF report with hypnogram, spectrogram, and statistics."""

    page_width, page_height = letter
    c = canvas.Canvas(filepath, pagesize=letter)

    # Save PIL images to temporary PNG files
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_hypno:
        hypnogram_img.save(tmp_hypno.name)
        hypno_path = tmp_hypno.name

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_spec:
        spectrogram_img.save(tmp_spec.name)
        spec_path = tmp_spec.name

    try:
        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(0.5 * inch, page_height - 0.5 * inch, "Sleep Report")

        # Add hypnogram
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.5 * inch, page_height - 1.0 * inch, "Hypnogram")
        c.drawImage(hypno_path, 0.5 * inch, page_height - 2.8 * inch, width=7.5 * inch, height=1.6 * inch)

        # Add spectrogram
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.5 * inch, page_height - 3.2 * inch, "Spectrogram")
        c.drawImage(spec_path, 0.5 * inch, page_height - 5.0 * inch, width=7.5 * inch, height=1.6 * inch)

        # Add statistics
        c.setFont("Helvetica-Bold", 11)
        c.drawString(0.5 * inch, page_height - 5.3 * inch, "Sleep Statistics")

        c.setFont("Courier", 9)
        text_y = page_height - 5.6 * inch
        for line in stats_text.split("\n"):
            if text_y < 0.5 * inch:
                break
            c.drawString(0.5 * inch, text_y, line)
            text_y -= 0.12 * inch

        c.save()
    finally:
        # Clean up temporary files
        try:
            os.unlink(hypno_path)
            os.unlink(spec_path)
        except:
            pass
