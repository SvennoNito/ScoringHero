import os
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import QFileDialog, QMessageBox
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import tempfile
from PIL import Image, ImageDraw, ImageFont


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
    """Create a beautiful hypnogram using PIL."""
    stages = np.array([stage["digit"] for stage in ui.stages], dtype=object)
    epoch_length_s = ui.config[0]["Epoch_length_s"]
    n_epochs = ui.numepo
    total_hours = n_epochs * epoch_length_s / 3600

    # Image dimensions
    width, height = 1200, 450
    margin_left, margin_right = 80, 40
    margin_top, margin_bottom = 50, 80

    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # Calculate plot area
    plot_left = margin_left
    plot_right = width - margin_right
    plot_top = margin_top
    plot_bottom = height - margin_bottom
    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top

    # Stage colors and positions
    stage_colors = {
        1: (139, 191, 86),      # Wake - yellow-green
        -1: (170, 188, 206),    # N1 - light blue
        -2: (64, 92, 121),      # N2 - blue
        -3: (11, 28, 44),       # N3 - dark blue
        0: (86, 191, 139),      # REM - green
    }

    stage_labels = {
        1: "Wake",
        -1: "N1",
        -2: "N2",
        -3: "N3",
        0: "REM",
    }

    stage_positions = {
        1: 0.8,
        -1: 0.6,
        -2: 0.4,
        -3: 0.2,
        0: 0.0,
    }

    # Draw outer box
    draw.rectangle([(plot_left, plot_top), (plot_right, plot_bottom)], outline="black", width=2)

    # Draw grid lines (vertical for hours)
    for h in range(int(total_hours) + 1):
        x = plot_left + (h / total_hours) * plot_width
        draw.line([(x, plot_top), (x, plot_bottom)], fill=(220, 220, 220), width=1)

    # Draw REM areas and sleep stage blocks
    for i, stage_value in enumerate(stages):
        if stage_value is not None:
            x_start = plot_left + (i / n_epochs) * plot_width
            x_end = plot_left + ((i + 1) / n_epochs) * plot_width
            y_pos = stage_positions.get(stage_value, 0.5)
            y_center = plot_top + y_pos * plot_height + 0.075 * plot_height
            y_top = y_center - 0.06 * plot_height
            y_bottom = y_center + 0.06 * plot_height

            # For REM, fill with red
            if stage_value == 0:
                draw.rectangle([(x_start, y_top), (x_end, y_bottom)], fill=(220, 100, 100), outline=None)

    # Draw black line following sleep stages
    line_points = []
    for i, stage_value in enumerate(stages):
        if stage_value is not None:
            x = plot_left + ((i + 0.5) / n_epochs) * plot_width
            y_pos = stage_positions.get(stage_value, 0.5)
            y = plot_top + y_pos * plot_height + 0.075 * plot_height
            line_points.append((x, y))

    if len(line_points) > 1:
        draw.line(line_points, fill="black", width=3)

    # Draw y-axis labels (stage names) on the left
    for stage in [1, -1, -2, -3, 0]:
        y_norm = stage_positions[stage]
        y = plot_top + y_norm * plot_height + 0.075 * plot_height
        label = stage_labels[stage]
        draw.text((10, int(y - 8)), label, fill="black")

    # Draw x-axis labels (hours)
    for h in range(int(total_hours) + 1):
        x = plot_left + (h / total_hours) * plot_width
        draw.text((int(x - 8), plot_bottom + 8), f"{h}h", fill="black")

    # Draw x-axis label
    draw.text((plot_left, plot_top - 35), "Time (0h = lights off)", fill="black")

    return img


def _create_whole_night_spectrogram(ui):
    """Create a whole-night spectrogram using PIL and cached periodogram data."""

    # Load the spectral colormap from spectral.txt
    colormap_path = os.path.join(ui.app_path, "spectral.txt")
    if not os.path.exists(colormap_path):
        raise FileNotFoundError(f"spectral.txt not found at {colormap_path}")

    rgb = np.loadtxt(colormap_path)  # (N, 3), 0-1

    # Use cached spectral data from ui
    power = np.log10(np.maximum(ui.power, 1e-30))[:, ui.freqsOI]  # log scale
    freqs = ui.freqs[ui.freqsOI]

    # Normalize power to [-1, 3] range and map to colormap
    power = np.clip(power, -1, 3)
    power_norm = (power - (-1)) / (3 - (-1))

    # Image dimensions
    n_epochs = ui.numepo
    n_freqs = len(freqs)
    pixel_scale = 3  # pixels per epoch/frequency
    img_width = n_epochs * pixel_scale
    img_height = n_freqs * pixel_scale
    margin_left, margin_right = 80, 50
    margin_top, margin_bottom = 50, 80
    total_width = img_width + margin_left + margin_right
    total_height = img_height + margin_top + margin_bottom

    # Create spectrogram image data
    spec_array = np.zeros((img_height, img_width, 3), dtype=np.uint8)

    for t in range(n_epochs):
        for f in range(n_freqs):
            norm_val = power_norm[t, f]
            colormap_idx = int(np.clip(norm_val * (len(rgb) - 1), 0, len(rgb) - 1))
            color = (rgb[colormap_idx] * 255).astype(np.uint8)

            # Fill pixels for this time-frequency bin
            for px in range(pixel_scale):
                for py in range(pixel_scale):
                    # Note: image y is inverted (0 at top), so we flip frequency axis
                    y_idx = img_height - 1 - (f * pixel_scale + py)
                    x_idx = t * pixel_scale + px
                    if 0 <= x_idx < img_width and 0 <= y_idx < img_height:
                        spec_array[y_idx, x_idx, :] = color

    # Convert array to PIL image
    spec_img = Image.fromarray(spec_array, mode="RGB")

    # Create base image with margins
    base_img = Image.new("RGB", (total_width, total_height), color="white")
    base_img.paste(spec_img, (margin_left, margin_top))

    # Draw on base image
    draw = ImageDraw.Draw(base_img)

    # Draw axes
    plot_left = margin_left
    plot_right = margin_left + img_width
    plot_top = margin_top
    plot_bottom = margin_top + img_height

    draw.rectangle([(plot_left, plot_top), (plot_right, plot_bottom)], outline="black", width=2)

    # Draw time axis labels
    total_hours = n_epochs * ui.config[0]["Epoch_length_s"] / 3600
    for h in range(int(total_hours) + 1):
        x = plot_left + (h / total_hours) * img_width
        draw.text((int(x - 8), plot_bottom + 8), f"{h}h", fill="black")

    # Draw frequency axis labels
    freq_step = max(1, int(n_freqs / 8))
    for i in range(0, n_freqs, freq_step):
        y = plot_bottom - (i / n_freqs) * img_height
        freq_label = f"{int(freqs[i])} Hz"
        draw.text((int(plot_left - 65), int(y - 8)), freq_label, fill="black")

    # Draw axis label for time
    draw.text((plot_left, plot_top - 35), "Time (0h = lights off)", fill="black")

    # Draw frequency label
    draw.text((10, int(plot_top + img_height // 2 - 40)), "Frequency", fill="black")

    return base_img


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
        "=" * 50,
        "SLEEP REPORT",
        "=" * 50,
        "",
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
        f"Wake:     {wake_epochs * epoch_length_min:5.1f} min ({wake_h:.1f} h) - {wake_pct:5.1f}%",
        f"N1:       {n1_min:5.1f} min ({n1_h:.1f} h) - {n1_pct:5.1f}%",
        f"N2:       {n2_min:5.1f} min ({n2_h:.1f} h) - {n2_pct:5.1f}%",
        f"N3:       {n3_min:5.1f} min ({n3_h:.1f} h) - {n3_pct:5.1f}%",
        f"REM:      {rem_min:5.1f} min ({rem_h:.1f} h) - {rem_pct:5.1f}%",
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

    lines.extend([
        "=" * 50,
    ])

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
