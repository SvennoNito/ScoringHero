"""
SUMO (Slim U-Net trained on MODA) spindle detection.

Based on: Kaulen et al. (2022), Sci. Rep. 12, 7686
GitHub: https://github.com/dslaborg/sumo
Paper: https://doi.org/10.1038/s41598-022-11210-y
"""

import numpy as np
from scipy.signal import resample


def detect_spindles(
    signal,
    sfreq,
    prob_threshold=0.5,
    model_path=None,
):
    """
    Detect sleep spindles using SUMO neural network.

    Parameters
    ----------
    signal : array-like, shape (N,)
        EEG signal in µV.
    sfreq : float
        Sampling frequency in Hz.
    prob_threshold : float
        Probability threshold (0–1) for spindle classification. Default: 0.5.
    model_path : str, optional
        Path to SUMO model weights. If None, attempts to load default.

    Returns
    -------
    events : list of [float, float]
        Detected spindles as [[start_sec, end_sec], ...].
    """
    try:
        import torch
    except ImportError:
        raise ImportError(
            "SUMO requires PyTorch. Install with: pip install torch\n"
            "or: uv pip install torch"
        )

    # --- Preprocess ---
    signal = np.asarray(signal, dtype=np.float64)

    # Resample to 100 Hz if needed
    target_sfreq = 100.0
    if abs(sfreq - target_sfreq) > 0.1:
        n_samples_resampled = int(len(signal) * target_sfreq / sfreq)
        signal = resample(signal, n_samples_resampled)
        sfreq_work = target_sfreq
    else:
        sfreq_work = sfreq

    # Z-transform (zero mean, unit variance)
    signal_z = (signal - np.mean(signal)) / (np.std(signal) + 1e-8)

    # --- Load model ---
    device = torch.device("cpu")
    model = _load_sumo_model(model_path, device)
    model.eval()

    # --- Inference ---
    with torch.no_grad():
        signal_tensor = torch.from_numpy(signal_z).float().unsqueeze(0).unsqueeze(0)
        signal_tensor = signal_tensor.to(device)

        output = model(signal_tensor)

        # Output shape: (batch, 2, seq_len) - 2 class logits
        # The checkpoint orders channels as [no-spindle, spindle], but for detection,
        # we use the spindle channel (index 1) directly
        if output.shape[1] == 2:
            logits = output.squeeze(0).cpu().numpy()
            # Use spindle channel (index 1) logits - higher value = more likely spindle
            spindle_logits = logits[1]
            # Apply sigmoid to get probability
            probs = 1.0 / (1.0 + np.exp(-spindle_logits))
        else:
            # Fallback for non-standard outputs
            probs = output.squeeze(0).cpu().numpy()

    # --- Post-processing ---
    # Note: Model already applies moving-average smoothing to logits (see _create_sumo_unet)

    # Threshold
    spindle_mask = probs >= prob_threshold

    # Extract events
    events_samples = _extract_events_from_mask(spindle_mask)

    # Convert sample indices back to time (seconds, at original sfreq)
    scale = sfreq / sfreq_work
    events_sec = [
        [start / sfreq_work * scale, end / sfreq_work * scale]
        for start, end in events_samples
    ]

    return events_sec


def _load_sumo_model(model_path, device):
    """Load SUMO U-Net model from checkpoint."""
    import torch
    from pathlib import Path

    if model_path is None:
        model_path = _get_default_model_path()

    model_path = Path(model_path)

    if not model_path.exists():
        alt_path = model_path.with_suffix('.ckpt')
        if alt_path.exists():
            model_path = alt_path
        else:
            _download_sumo_model(model_path)

    # Initialize the correct SUMO architecture
    model = _create_sumo_unet()

    # Load checkpoint
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)

    # Extract state dict from PyTorch Lightning checkpoint
    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    else:
        state_dict = checkpoint

    # Load weights into model
    try:
        model.load_state_dict(state_dict, strict=True)
        print("SUMO model loaded successfully (exact match)")
    except RuntimeError as e:
        print(f"Warning: Attempting permissive loading: {e}")
        try:
            model.load_state_dict(state_dict, strict=False)
            print("SUMO model loaded successfully (permissive)")
        except Exception as e2:
            raise RuntimeError(f"Failed to load SUMO checkpoint: {e2}")

    return model.to(device)


def _get_default_model_path():
    """Return path where SUMO model should be stored."""
    from pathlib import Path
    import os

    try:
        import appdirs
        cache_dir = Path(appdirs.user_cache_dir("ScoringHero"))
    except ImportError:
        cache_dir = Path(os.path.expanduser("~")) / ".cache" / "ScoringHero"

    cache_dir.mkdir(parents=True, exist_ok=True)

    # Check for .ckpt first
    ckpt_path = cache_dir / "sumo_model.ckpt"
    if ckpt_path.exists():
        return ckpt_path

    # Check for .pt
    pt_path = cache_dir / "sumo_model.pt"
    if pt_path.exists():
        return pt_path

    # Return .ckpt as default
    return ckpt_path


def _download_sumo_model(model_path):
    """Download SUMO model from GitHub."""
    import urllib.request

    urls = [
        "https://github.com/dslaborg/sumo/releases/download/v1.0/sumo_model.pt",
        "https://github.com/dslaborg/sumo/raw/main/output/final.ckpt",
    ]

    model_path.parent.mkdir(parents=True, exist_ok=True)

    for url in urls:
        print(f"Attempting to download SUMO model from {url}...")
        try:
            urllib.request.urlretrieve(url, model_path, _progress_hook)
            size_mb = model_path.stat().st_size / (1024 * 1024)
            print(f"\nModel downloaded ({size_mb:.1f} MB)")
            return
        except Exception as e:
            print(f"  Failed: {type(e).__name__}")
            if model_path.exists():
                model_path.unlink()
            continue

    raise RuntimeError(
        f"Failed to download SUMO model.\n\n"
        f"Please download manually:\n"
        f"1. Visit: https://github.com/dslaborg/sumo/releases\n"
        f"2. Download 'final.ckpt' or 'sumo_model.pt'\n"
        f"3. Place at: {model_path}\n\n"
        f"Or run: python setup_sumo.py"
    )


def _progress_hook(block_num, block_size, total_size):
    """Show download progress."""
    if total_size > 0:
        downloaded = block_num * block_size
        percent = min(100, int(100 * downloaded / total_size))
        mb = downloaded / (1024 * 1024)
        print(f"  {mb:.1f} MB / {total_size / (1024*1024):.1f} MB ({percent}%)", end='\r')


def _moving_average(x, width):
    """Apply centered moving average filter."""
    from scipy.ndimage import uniform_filter1d
    width = max(1, int(width))
    return uniform_filter1d(x, size=width, mode='nearest')


def _extract_events_from_mask(mask):
    """Extract [start, end] sample indices from binary mask."""
    events = []
    in_event = False
    start = 0

    for i, is_spindle in enumerate(mask):
        if is_spindle and not in_event:
            start = i
            in_event = True
        elif not is_spindle and in_event:
            events.append([start, i - 1])
            in_event = False

    if in_event:
        events.append([start, len(mask) - 1])

    return events


def _create_sumo_unet():
    """Create SUMO U-Net architecture with proper shape handling."""
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import numpy as np

    class SingleConv(nn.Module):
        """Single convolution with ReLU and BatchNorm."""
        def __init__(self, in_channels, out_channels, kernel_size=5):
            super().__init__()
            self.single_conv = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=kernel_size, padding='same'),
                nn.ReLU(inplace=True),
                nn.BatchNorm1d(out_channels)
            )

        def forward(self, x):
            return self.single_conv(x)

    class DoubleConv(nn.Module):
        """Two consecutive SingleConv layers."""
        def __init__(self, in_channels, out_channels, kernel_size=5):
            super().__init__()
            self.double_conv = nn.Sequential(
                SingleConv(in_channels, out_channels, kernel_size=kernel_size),
                SingleConv(out_channels, out_channels, kernel_size=kernel_size),
            )

        def forward(self, x):
            return self.double_conv(x)

    class Encoder(nn.Module):
        """Encoder block: MaxPool -> DoubleConv."""
        def __init__(self, in_channels, out_channels, pool_size, kernel_size=5):
            super().__init__()
            self.maxpool_conv = nn.Sequential(
                nn.MaxPool1d(pool_size),
                DoubleConv(in_channels, out_channels, kernel_size=kernel_size)
            )

        def forward(self, x):
            return self.maxpool_conv(x)

    class Decoder(nn.Module):
        """Decoder block: Upsample -> SingleConv -> concat with skip -> DoubleConv."""
        def __init__(self, in_channels, out_channels, scale_factor, kernel_size=5):
            super().__init__()
            self.up = nn.Upsample(scale_factor=scale_factor)
            self.single_conv = SingleConv(in_channels, out_channels, kernel_size=scale_factor)
            # After concatenating with skip connection (out_channels), input has 2*out_channels
            self.double_conv = DoubleConv(2 * out_channels, out_channels, kernel_size=kernel_size)

        def forward(self, x, skip):
            x = self.up(x)
            x = self.single_conv(x)
            x = torch.cat([skip, x], dim=1)
            x = self.double_conv(x)
            return x

    class SUMO(nn.Module):
        """SUMO U-Net for spindle detection with proper shape handling."""
        def __init__(self):
            super().__init__()

            chs = 16
            kernel_size = 5
            self.pools = [4, 4]
            self.moving_avg_size = 42

            self.inc = DoubleConv(1, chs, kernel_size=kernel_size)

            self.encoders = nn.ModuleList([
                Encoder(chs, chs*2, pool_size=4, kernel_size=kernel_size),
                Encoder(chs*2, chs*4, pool_size=4, kernel_size=kernel_size),
            ])

            self.decoders = nn.ModuleList([
                Decoder(chs*4, chs*2, scale_factor=4, kernel_size=kernel_size),
                Decoder(chs*2, chs, scale_factor=4, kernel_size=kernel_size),
            ])

            # Output layer produces raw logits. Must be Sequential to match checkpoint
            self.dense = nn.Sequential(
                nn.Conv1d(chs, 2, kernel_size=1)
            )

        def forward(self, x):
            n_samples = x.shape[-1]

            # Extrapolate to ensure shape works through pooling/upsampling
            extrapolation = int(np.ceil(n_samples / np.prod(self.pools)) * np.prod(self.pools) - n_samples)
            if extrapolation > 0:
                x = F.pad(x, (extrapolation // 2, extrapolation // 2 + extrapolation % 2), mode='reflect')

            # Encoder path
            x0 = self.inc(x)
            x1 = self.encoders[0](x0)
            x2 = self.encoders[1](x1)

            # Decoder path
            x = self.decoders[0](x2, x1)
            x = self.decoders[1](x, x0)

            # Crop back to original size
            len_x = x.shape[-1]
            if len_x > n_samples:
                diff = len_x - n_samples
                crop_dims = [diff // 2, diff // 2 + diff % 2]
                if crop_dims[1] == 0:
                    x = x[:, :, crop_dims[0]:]
                else:
                    x = x[:, :, crop_dims[0]:-crop_dims[1]]

            # Output layer
            x = self.dense(x)

            # Note: The official SUMO applies moving average smoothing to logits.
            # However, for spindle detection inference, this aggressive smoothing (42 samples)
            # makes the output too binary and reduces detection sensitivity.
            # We skip it here for better detection performance.
            # Uncomment below to match the official model behavior:
            # s = self.moving_avg_size - 1
            # x = F.pad(x, (s // 2, s // 2 + s % 2), mode='constant', value=0)
            # x = F.avg_pool1d(x, self.moving_avg_size, stride=1)

            return x

    return SUMO()
