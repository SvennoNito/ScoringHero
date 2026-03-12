import numpy as np


def compute_morlet_tf(signal, srate, freqs, n_cycles=None, L2normalize=False):
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
        Centre frequencies in Hz.
    n_cycles : float, array-like, or None
        Number of wavelet cycles per frequency.  When None (default) a
        variable scheme is used: n_cycles = max(3, freq / 2).  This gives
        better temporal resolution at low frequencies (individual slow
        waves are sharply localised) while preserving good frequency
        resolution at higher frequencies (spindles, beta, gamma).
        Pass a scalar to use the same value for every frequency.
    normalize : bool
        If True, L2-normalize each wavelet so it has unit energy. This
        makes power values comparable across frequencies. If False, the
        raw (unnormalized) power is returned.

    Returns
    -------
    power : 2-D ndarray, shape (n_freqs, n_samples)
        Instantaneous power (squared magnitude of the analytic signal).
    """
    freqs = np.asarray(freqs)

    if n_cycles is None:
        n_cycles_arr = np.maximum(3.0, freqs / 2.0)
    elif np.isscalar(n_cycles):
        n_cycles_arr = np.full(len(freqs), float(n_cycles))
    else:
        n_cycles_arr = np.asarray(n_cycles, dtype=float)

    n_samples = len(signal)
    signal_fft = np.fft.fft(signal)
    fft_freqs = np.fft.fftfreq(n_samples, d=1.0 / srate)

    power = np.empty((len(freqs), n_samples), dtype=np.float64)
    for i, freq in enumerate(freqs):
        sigma_f = freq / n_cycles_arr[i]
        wavelet_fft = np.exp(-0.5 * ((fft_freqs - freq) / sigma_f) ** 2)
        if L2normalize:
            wavelet_fft /= np.sqrt(np.sum(wavelet_fft ** 2))
        analytic = np.fft.ifft(signal_fft * wavelet_fft)
        power[i] = np.abs(analytic) ** 2

    return power
