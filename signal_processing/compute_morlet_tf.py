import numpy as np


def compute_morlet_tf(signal, srate, freqs, n_cycles=6):
    """Compute time-frequency power via Morlet wavelet convolution (FFT-based).

    For each frequency the signal is convolved with a complex Morlet wavelet
    whose bandwidth is set by n_cycles. The FFT of the signal is computed
    once and then multiplied by each wavelet's frequency-domain Gaussian,
    making this O(F * N log N) in total.

    Parameters
    ----------
    signal : 1-D ndarray, shape (n_samples,)
        EEG signal for one epoch (may include extension on either side).
    srate : float
        Sampling rate in Hz.
    freqs : 1-D ndarray
        Centre frequencies in Hz (e.g. np.arange(0.25, 45.25, 0.25)).
    n_cycles : float
        Number of wavelet cycles, controlling the time-frequency trade-off.
        A value of 6 is a common default.

    Returns
    -------
    power : 2-D ndarray, shape (n_freqs, n_samples)
        Instantaneous power (squared magnitude of the analytic signal).
    """
    n_samples = len(signal)
    signal_fft = np.fft.fft(signal)
    fft_freqs = np.fft.fftfreq(n_samples, d=1.0 / srate)

    power = np.empty((len(freqs), n_samples), dtype=np.float64)
    for i, freq in enumerate(freqs):
        # Gaussian width in frequency domain: sigma_f = freq / n_cycles
        sigma_f = freq / n_cycles
        wavelet_fft = np.exp(-0.5 * ((fft_freqs - freq) / sigma_f) ** 2)
        wavelet_fft /= np.sqrt(np.sum(wavelet_fft ** 2))  # L2-normalize
        analytic = np.fft.ifft(signal_fft * wavelet_fft)
        power[i] = np.abs(analytic) ** 2

    return power
