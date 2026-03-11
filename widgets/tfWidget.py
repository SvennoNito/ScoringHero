import os
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QWidget

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

        self.axes = self.graphics.addPlot()
        self.axes.setLabel("left", "Freq (Hz)")
        self.axes.setLabel("bottom", "Time (s)")

        self.img = pg.ImageItem()
        self.img.setColorMap(self._load_colormap(app_path))
        self.axes.addItem(self.img)

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
    def _render(self, eeg_data, times_and_indices, this_epoch, srate, freqs,
                norm_median, norm_iqr):
        """Compute Morlet power for this_epoch, z-score it, and update the ImageItem.

        Each frequency band is normalized independently using the per-frequency
        median and IQR of log10 power across the entire night (robust z-score):

            z[f, t] = (log10(power[f, t]) - median_night[f]) / IQR_night[f]
        """
        epoch_times, epoch_indices, _ = times_and_indices[this_epoch]

        # --- compute power on the full extended epoch signal -----------
        signal    = eeg_data[0][epoch_indices].astype(np.float64)
        power_ext = compute_morlet_tf(signal, srate, freqs)  # (n_freqs, n_ext)

        # --- log10 transform ------------------------------------------
        power_log = np.log10(np.maximum(power_ext, 1e-30))

        # --- robust z-score (per frequency, using night-wide stats) ---
        # norm_median and norm_iqr are (n_freqs,); broadcast over time axis.
        power_z = (power_log - norm_median[:, np.newaxis]) / norm_iqr[:, np.newaxis]
        # power_z = power_log

        # --- update ImageItem (col-major: first axis = x = time) ------
        # Transpose so shape becomes (n_ext, n_freqs): x=time, y=freq.
        self.img.setImage(power_z.T)
        self.img.setLevels([-3, 3])   # symmetric around zero; ±3 IQR units

        # --- axis ticks -----------------------------------------------
        n_times   = power_ext.shape[1]
        n_freqs   = len(freqs)
        freq_step = freqs[1] - freqs[0]

        # Time axis: match the extended time range shown in the EEG panel
        t_positions = np.linspace(0, n_times, 7).astype(int)
        t_values    = np.linspace(epoch_times[0], epoch_times[-1], 7)
        time_ticks  = [
            (int(pos), f"{val:.0f}s")
            for pos, val in zip(t_positions, t_values)
            if pos < n_times
        ]
        self.axes.getAxis("bottom").setTicks([time_ticks])

        # Frequency axis: labels every 5 Hz
        desired_hz  = np.arange(0, freqs[-1] + 1, 5)
        freq_ticks  = [
            (f / freq_step, f"{int(f)}")
            for f in desired_hz
            if f <= freqs[-1]
        ]
        self.axes.getAxis("left").setTicks([freq_ticks])

        self.axes.setXRange(0, n_times, padding=0)
        self.axes.setYRange(0, n_freqs, padding=0)

    # ------------------------------------------------------------------
    def draw_tf(self, eeg_data, times_and_indices, this_epoch, srate, freqs,
                norm_median, norm_iqr):
        """First-time draw (called from redraw_gui)."""
        self._render(eeg_data, times_and_indices, this_epoch, srate, freqs,
                     norm_median, norm_iqr)

    def update_tf(self, eeg_data, times_and_indices, this_epoch, srate, freqs,
                  norm_median, norm_iqr):
        """Lightweight update on every epoch change (called from refresh_gui)."""
        self._render(eeg_data, times_and_indices, this_epoch, srate, freqs,
                     norm_median, norm_iqr)
