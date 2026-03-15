import os
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from signal_processing.compute_morlet_tf import compute_morlet_tf


class TFWidget(QWidget):
    """Time-frequency panel using Morlet wavelets.

    Displays instantaneous power (log10) for a single EEG channel across
    the frequencies defined by ui.tf_freqs, covering the current epoch.
    The extended-epoch signal (including left/right padding) is used for
    the convolution so that edge artefacts are pushed outside the core
    display window.
    """

    def __init__(self, centralWidget, app_path):
        super().__init__()
        pg.setConfigOptions(imageAxisOrder="col-major")
        self.graphics = pg.GraphicsLayoutWidget(centralWidget)
        self.graphics.setObjectName("TFWidget")
        self.graphics.setBackground("w")
        self.graphics.ci.layout.setContentsMargins(0, 0, 0, 0)
        self.graphics.ci.layout.setSpacing(0)

        self.axes = self.graphics.addPlot()
        self.axes.setLabel("left", "")
        self.axes.setLabel("bottom", "")
        left_ax = self.axes.getAxis("left")
        left_ax.setStyle(showValues=True, tickLength=0)
        left_ax.setWidth(35)
        tick_font = QFont()
        tick_font.setPixelSize(10)
        left_ax.setTickFont(tick_font)
        self.axes.getAxis("bottom").setStyle(tickLength=-8)

        self._colormap = self._load_colormap(app_path)
        self.img = pg.ImageItem()
        self.img.setColorMap(self._colormap)
        self.axes.addItem(self.img)
        self._freq_labels = []  # kept for cleanup; no longer drawn inside the plot
        #self._hz_label = pg.TextItem(text="Hz", color=(150, 150, 150), anchor=(0.5, 0))
        #self._hz_label.setParentItem(left_ax)
        #self._hz_label.setPos(17, 2)
        self._freq_scale = "Logarithmic"  # default frequency scale
        self._freqs_filtered = None  # current filtered frequencies
        self._ref_lines = []  # horizontal reference lines at fixed Hz values
        self._prev_n_times = None  # tracks n_times to detect image size changes

        # self.axes.setLabel("left", "Hz", units=None)
        left_ax = self.axes.getAxis("left")
        # left_ax.setLabel(text="Hz", **{"font-size": "8pt", "color": "#999"})
        # left_ax.setStyle(tickTextOffset=2)        
        #left_ax.label.setFixedWidth(20)   # important: fixed geometry
        # left_ax.setWidth(30)              # keep same as before        

        # Internal colorbar: narrow ImageItem + two TextItem labels
        self._cbar_img = pg.ImageItem()
        self._cbar_img.setColorMap(self._colormap)
        self._cbar_img.setZValue(10)
        self.axes.addItem(self._cbar_img)
        self._cbar_min_label = pg.TextItem(color=(0, 0, 0), anchor=(0.5, 0))
        self._cbar_max_label = pg.TextItem(color=(0, 0, 0), anchor=(0.5, 1))
        self._cbar_min_label.setZValue(11)
        self._cbar_max_label.setZValue(11)
        self.axes.addItem(self._cbar_min_label)
        self.axes.addItem(self._cbar_max_label)

        # Channel label overlay (same style as DisplayedEpochWidget)
        self._channel_label = QLabel(self.graphics)
        self._channel_label.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        font = QFont()
        font.setBold(True)
        self._channel_label.setFont(font)
        self._channel_label.setStyleSheet("color: white;")
        self._channel_label.setAttribute(Qt.WA_TranslucentBackground)
        self._channel_label.setObjectName("tf_channel_label")
        channel_layout = QVBoxLayout(self.graphics)
        channel_layout.addWidget(self._channel_label)

    @staticmethod
    def _load_colormap(app_path):
        """Build a pg.ColorMap from spectral.txt (RGB floats 0-1, one row per stop).

        The file is resolved relative to app_path, which equals sys._MEIPASS
        inside a PyInstaller .exe and the project root during normal execution.
        spectral.txt must be listed in the PyInstaller .spec datas so it is
        bundled into sys._MEIPASS at build time.
        """
        colormap_path = os.path.join(app_path, "spectral.txt")
        rgb = np.loadtxt(colormap_path)                          # (N, 3), 0-1
        rgba = np.hstack([
            (rgb * 255).clip(0, 255).astype(np.uint8),
            np.full((len(rgb), 1), 255, dtype=np.uint8),         # alpha = opaque
        ])
        positions = np.linspace(0.0, 1.0, len(rgb))
        return pg.ColorMap(positions, rgba)

    # ------------------------------------------------------------------
    _x_unit_format = {
        "Seconds": {"format": "{:.0f} s", "div": 1},
        "Minutes": {"format": "{:.2f} min", "div": 60},
        "Hours": {"format": "{:.3f} h", "div": 3600},
    }

    _default_levels = {
        "Raw Power": [-1, 3],
        "L2-Normalized Power": [-1, 3],
        "Z-Standardized Power": [-3, 3],
        "dB (median baseline)": [0, 20],
    }

    def _render(self, eeg_data, times_and_indices, this_epoch, srate, freqs,
                norm_median, norm_iqr, norm_rms, norm_median_linear=None, display_mode="Z-scored Power",
                freq_scale="Logarithmic", freq_limits=None,
                time_unit="Seconds", epoch_length=30, tf_channel_idx=0, channel_label="",
                power_limits=None):
        """Compute Morlet power for this_epoch and update the ImageItem.

        Parameters
        ----------
        display_mode : str
            How to display the time-frequency power:
            - "Raw Power": log10(power) as-is
            - "Normalized Power": L2-normalized log10(power)
            - "Z-scored Power": robust z-score using night-wide median/IQR
        freq_scale : str
            Frequency axis scale: "Logarithmic" or "Linear"
        freq_limits : list or None
            Frequency limits [min_hz, max_hz] to display. If None, use full range.
        """
        epoch_times, epoch_indices, _ = times_and_indices[this_epoch]

        # --- generate frequency grid based on scale preference ----------
        if freq_scale == "Logarithmic":
            freqs_for_compute = freqs  # already geomspace from load_cache
            norm_med = norm_median
            norm_iq = norm_iqr
        else:
            # Linear-spaced grid over the same range
            freqs_for_compute = np.linspace(freqs[0], freqs[-1], len(freqs))
            # Re-interpolate normalization stats onto the new linear grid
            norm_med = np.interp(freqs_for_compute, freqs, norm_median)
            norm_iq = np.interp(freqs_for_compute, freqs, norm_iqr)
            norm_rms = np.interp(freqs_for_compute, freqs, norm_rms)
            if norm_median_linear is not None:
                norm_median_linear = np.interp(freqs_for_compute, freqs, norm_median_linear)

        # --- compute power on the full extended epoch signal -----------
        signal    = eeg_data[tf_channel_idx][epoch_indices].astype(np.float64)
        # normalize = display_mode in ("L2-Normalized Power", "Z-Standardized Power")
        normalize = display_mode in ("Z-Standardized Power")
        power_ext = compute_morlet_tf(signal, srate, freqs_for_compute,
                                      L2normalize=normalize)  # (n_freqs, n_ext)

        # --- log10 power (always, regardless of frequency axis scale) --
        power_transformed = np.log10(np.maximum(power_ext, 1e-30))

        # --- apply display mode normalization -------------------------
        if display_mode == "Raw Power":
            power_display = power_transformed

        elif display_mode == "L2-Normalized Power":
            power_display = power_transformed / norm_rms[:, np.newaxis]

        elif display_mode == "Z-Standardized Power":
            # robust z-score using night-wide log-power median/IQR per frequency
            power_display = (power_transformed - norm_med[:, np.newaxis]) / norm_iq[:, np.newaxis]

        elif display_mode == "dB (median baseline)":
            # dB relative to median baseline: 10 * log10(power / baseline)
            # = 10 * (log10(power) - log10(baseline))
            baseline_log = np.log10(np.maximum(norm_median_linear, 1e-30))
            power_display = 10 * (power_transformed - baseline_log[:, np.newaxis])

        else:
            power_display = power_transformed

        # --- resolve color levels (from config or default per display mode) ---
        if power_limits and display_mode in power_limits:
            levels = list(power_limits[display_mode])
        else:
            levels = list(self._default_levels.get(display_mode, [-1, 3]))

        # --- filter to frequency limits if specified -------------------
        if freq_limits is not None:
            freq_min, freq_max = freq_limits
            mask = (freqs_for_compute >= freq_min) & (freqs_for_compute <= freq_max)
            freqs_filtered = freqs_for_compute[mask]
            power_display = power_display[mask, :]
        else:
            freqs_filtered = freqs_for_compute

        # --- update ImageItem (col-major: first axis = x = time) ------
        # Transpose so shape becomes (n_ext, n_freqs): x=time, y=freq.
        self.img.setImage(power_display.T)
        self.img.setLevels(levels)
        self._channel_label.setText(channel_label)

        # --- axis ticks -----------------------------------------------
        n_times = power_ext.shape[1]
        n_freqs = len(freqs_filtered)

        # Time axis: same tick positions and labels as the main signal panel
        unit_fmt = self._x_unit_format[time_unit]
        t_start, t_end = epoch_times[0], epoch_times[-1]
        tick_step = epoch_length / 5
        tick_seconds = np.round(np.arange(0, t_end, tick_step), 1)
        # Map real-time seconds to image pixel positions
        time_ticks = []
        for t in tick_seconds:
            if t_start <= t <= t_end:
                pos = (t - t_start) / (t_end - t_start) * n_times
                time_ticks.append((int(pos), unit_fmt["format"].format(t / unit_fmt["div"])))
        self.axes.getAxis("bottom").setTicks([time_ticks])

        freqs_changed = (
            self._freqs_filtered is None
            or len(freqs_filtered) != len(self._freqs_filtered)
            or not np.array_equal(freqs_filtered, self._freqs_filtered)
            or self._freq_scale != freq_scale
            or self._prev_n_times != n_times
        )
        self._freq_scale = freq_scale
        self._freqs_filtered = freqs_filtered
        self._prev_n_times = n_times

        if freqs_changed:
            self._update_freq_decorations(freqs_filtered, freq_scale, n_times, n_freqs)

        # --- internal colorbar -------------------------------------------
        cbar_width = max(1, int(n_times * 0.012))
        cbar_margin = n_freqs * 0.15
        cbar_y = cbar_margin
        cbar_height = n_freqs - 2 * cbar_margin
        cbar_x = n_times - cbar_width - max(1, int(n_times * 0.005))
        gradient = np.linspace(levels[0], levels[1], max(2, int(cbar_height))).reshape(-1, 1)
        gradient = np.repeat(gradient, cbar_width, axis=1)
        self._cbar_img.setImage(gradient.T)
        self._cbar_img.setLevels(levels)
        self._cbar_img.setRect(cbar_x, cbar_y, cbar_width, cbar_height)
        self._cbar_min_label.setText(f"{levels[0]:.1f}")
        self._cbar_max_label.setText(f"{levels[1]:.1f}")
        cbar_center_x = cbar_x + cbar_width / 2
        self._cbar_min_label.setPos(cbar_center_x, cbar_y)
        self._cbar_max_label.setPos(cbar_center_x, cbar_y + cbar_height)

    # ------------------------------------------------------------------
    def _update_freq_decorations(self, freqs_filtered, freq_scale, n_times, n_freqs):
        """Rebuild freq labels and ref lines. Only called when the frequency axis changes."""
        for lbl in self._freq_labels:
            self.axes.removeItem(lbl)
        self._freq_labels = []
        for line in self._ref_lines:
            self.axes.removeItem(line)
        self._ref_lines = []

        hi = freqs_filtered[-1]
        if freq_scale == "Logarithmic":
            desired_hz = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0]
        elif hi <= 30:
            desired_hz = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
        else:
            desired_hz = list(np.arange(10.0, hi + 1, 10.0))
            desired_hz = [f for f in desired_hz if f <= hi]

        freq_ticks = []
        ref_pen = pg.mkPen(color=(255, 255, 255, 160), width=1.0,
                           style=Qt.PenStyle.DotLine)
        for f in desired_hz:
            if freqs_filtered[0] <= f <= freqs_filtered[-1]:
                idx = int(np.argmin(np.abs(freqs_filtered - f)))
                freq_ticks.append((idx, f"{f:g}Hz"))
                ref_idx = float(np.interp(f, freqs_filtered, np.arange(n_freqs)))
                line = pg.InfiniteLine(pos=ref_idx, angle=0, pen=ref_pen)
                line.setZValue(9)
                self.axes.addItem(line)
                self._ref_lines.append(line)
        self.axes.getAxis("left").setTicks([freq_ticks])
        self.axes.setXRange(0, n_times, padding=0)
        self.axes.setYRange(0, n_freqs, padding=0)

    # ------------------------------------------------------------------
    def draw_tf(self, eeg_data, times_and_indices, this_epoch, srate, freqs,
                norm_median, norm_iqr, norm_rms, norm_median_linear=None, display_mode="Z-scored Power",
                freq_scale="Logarithmic", freq_limits=None,
                time_unit="Seconds", epoch_length=30, tf_channel_idx=0, channel_label="",
                power_limits=None):
        """First-time draw (called from redraw_gui)."""
        self._render(eeg_data, times_and_indices, this_epoch, srate, freqs,
                     norm_median, norm_iqr, norm_rms, norm_median_linear, display_mode, freq_scale, freq_limits,
                     time_unit, epoch_length, tf_channel_idx, channel_label, power_limits)

    def update_tf(self, eeg_data, times_and_indices, this_epoch, srate, freqs,
                  norm_median, norm_iqr, norm_rms, norm_median_linear=None, display_mode="Z-scored Power",
                  freq_scale="Logarithmic", freq_limits=None,
                  time_unit="Seconds", epoch_length=30, tf_channel_idx=0, channel_label="",
                  power_limits=None):
        """Lightweight update on every epoch change (called from refresh_gui)."""
        self._render(eeg_data, times_and_indices, this_epoch, srate, freqs,
                     norm_median, norm_iqr, norm_rms, norm_median_linear, display_mode, freq_scale, freq_limits,
                     time_unit, epoch_length, tf_channel_idx, channel_label, power_limits)
