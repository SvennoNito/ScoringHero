import os
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
from PIL import Image


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
    """Create a beautiful hypnogram figure and return as PIL Image."""
    fig, ax = plt.subplots(figsize=(10, 3), dpi=150)

    stage_colors = {
        -4: "#bf5656",  # N4
        -3: "#0b1c2c",  # N3
        -2: "#405c79",  # N2
        -1: "#aabcce",  # N1
        0: "#56bf8b",   # REM
        1: "#8bbf56",   # Wake
    }

    # Get stages and times
    stages = np.array([stage["digit"] for stage in ui.stages])
    times = np.arange(0, ui.numepo) * ui.config[0]["Epoch_length_s"] / 3600  # hours

    # Draw rectangles for each stage
    epoch_length = ui.config[0]["Epoch_length_s"] / 3600
    for i, stage_value in enumerate(stages):
        if stage_value is not None:
            color = stage_colors.get(stage_value, "#cccccc")
            ax.barh(0, epoch_length, left=times[i], height=0.8, color=color, edgecolor="black", linewidth=0.5)

    ax.set_xlim(0, times[-1] + epoch_length)
    ax.set_ylim(-0.5, 0.5)
    ax.set_xlabel("Time (hours)", fontsize=10)
    ax.set_ylabel("Sleep Stage", fontsize=10)
    ax.set_yticks([])
    ax.grid(axis="x", alpha=0.3)

    # Create legend
    legend_labels = ["Wake", "N1", "N2", "N3", "N4", "REM"]
    legend_colors = [stage_colors[i] for i in [1, -1, -2, -3, -4, 0]]
    ax.legend(
        [plt.Rectangle((0, 0), 1, 1, fc=color) for color in legend_colors],
        legend_labels,
        loc="upper left",
        bbox_to_anchor=(1.01, 1),
        fontsize=9,
    )

    plt.tight_layout()

    # Convert to PIL Image
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    img = Image.open(buf)
    img.load()
    buf.close()
    plt.close(fig)

    return img


def _create_whole_night_spectrogram(ui):
    """Create a whole-night spectrogram using cached periodogram data and spectral colormap."""

    # Load the spectral colormap from spectral.txt
    colormap_path = os.path.join(ui.app_path, "spectral.txt")
    if not os.path.exists(colormap_path):
        raise FileNotFoundError(f"spectral.txt not found at {colormap_path}")

    rgb = np.loadtxt(colormap_path)  # (N, 3), 0-1
    cmap = LinearSegmentedColormap.from_list("spectral", rgb)

    # Use cached spectral data from ui
    # ui.power shape: (n_epochs, n_freqs)
    # ui.freqs: frequency array
    # ui.freqsOI: indices of frequencies of interest
    power = np.log10(np.maximum(ui.power, 1e-30))[:, ui.freqsOI]  # log scale
    freqs = ui.freqs[ui.freqsOI]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 3.5), dpi=150)

    # Plot spectrogram
    n_epochs = ui.numepo
    times_hours = np.arange(n_epochs) * ui.config[0]["Epoch_length_s"] / 3600

    # Transpose for proper pcolormesh (frequencies on y-axis)
    im = ax.pcolormesh(
        times_hours,
        freqs,
        power.T,
        cmap=cmap,
        shading="auto",
    )

    ax.set_xlabel("Time (hours)", fontsize=10)
    ax.set_ylabel("Frequency (Hz)", fontsize=10)
    ax.set_title("Spectrogram (Pwelch)", fontsize=12, fontweight="bold")

    # Set reasonable frequency limit for visibility
    freq_max = min(freqs[-1], 50)
    ax.set_ylim(freqs[0], freq_max)

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Power (log10)", fontsize=9)

    plt.tight_layout()

    # Convert to PIL Image
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
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
    n4_epochs = np.sum(stages == -4)
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
    n4_min = n4_epochs * epoch_length_min
    rem_min = rem_epochs * epoch_length_min

    # Latencies (time to first N2/N3 sleep, REM latency)
    n2_or_n3_mask = (stages == -2) | (stages == -3)
    n2_onset_idx = np.where(n2_or_n3_mask)[0]
    n2_latency_min = None
    if len(n2_onset_idx) > 0:
        n2_latency_min = n2_onset_idx[0] * epoch_length_min

    rem_onset_idx = np.where(stages == 0)[0]
    rem_latency_min = None
    if len(rem_onset_idx) > 0:
        rem_latency_min = rem_onset_idx[0] * epoch_length_min

    # Build text report
    lines = [
        "=" * 50,
        "SLEEP REPORT",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "SLEEP STATISTICS",
        "-" * 50,
        f"Total Sleep Time (TST):        {tst_min:.1f} min ({tst_min/60:.1f} h)",
        f"Total Recording Time (TRT):    {trt_min:.1f} min ({trt_min/60:.1f} h)",
        f"Sleep Efficiency:              {sleep_efficiency:.1f}%",
        "",
        "SLEEP STAGE DISTRIBUTION",
        "-" * 50,
        f"Wake:                          {wake_epochs} epochs  {wake_epochs*epoch_length_min:.1f} min  {wake_epochs/scored_epochs*100:.1f}%",
        f"N1:                            {n1_epochs} epochs  {n1_min:.1f} min  {n1_epochs/scored_epochs*100:.1f}%",
        f"N2:                            {n2_epochs} epochs  {n2_min:.1f} min  {n2_epochs/scored_epochs*100:.1f}%",
        f"N3:                            {n3_epochs} epochs  {n3_min:.1f} min  {n3_epochs/scored_epochs*100:.1f}%",
        f"N4:                            {n4_epochs} epochs  {n4_min:.1f} min  {n4_epochs/scored_epochs*100:.1f}%",
        f"REM:                           {rem_epochs} epochs  {rem_min:.1f} min  {rem_epochs/scored_epochs*100:.1f}%",
        "",
        "LATENCIES",
        "-" * 50,
    ]

    if n2_latency_min is not None:
        lines.append(f"Time to first N2/N3 sleep:     {n2_latency_min:.1f} min")
    else:
        lines.append(f"Time to first N2/N3 sleep:     N/A")

    if rem_latency_min is not None:
        lines.append(f"REM latency:                   {rem_latency_min:.1f} min")
    else:
        lines.append(f"REM latency:                   N/A")

    lines.extend([
        "=" * 50,
    ])

    return "\n".join(lines)


def _create_pdf_report(filepath, hypnogram_img, spectrogram_img, stats_text, ui):
    """Create a PDF report with hypnogram, spectrogram, and statistics."""

    import tempfile
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

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
        c.drawString(0.5 * inch, page_height - 1 * inch, "Hypnogram")
        c.drawImage(hypno_path, 0.5 * inch, page_height - 2.5 * inch, width=7.5 * inch, height=1.2 * inch)

        # Add spectrogram
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.5 * inch, page_height - 3.6 * inch, "Spectrogram")
        c.drawImage(spec_path, 0.5 * inch, page_height - 5.2 * inch, width=7.5 * inch, height=1.4 * inch)

        # Add statistics
        c.setFont("Helvetica-Bold", 12)
        c.drawString(0.5 * inch, page_height - 5.6 * inch, "Sleep Statistics")

        c.setFont("Courier", 9)
        text_y = page_height - 5.9 * inch
        for line in stats_text.split("\n"):
            if text_y < 0.5 * inch:
                break
            c.drawString(0.5 * inch, text_y, line)
            text_y -= 0.12 * inch

        c.save()
    finally:
        # Clean up temporary files
        import os as _os
        try:
            _os.unlink(hypno_path)
            _os.unlink(spec_path)
        except:
            pass
