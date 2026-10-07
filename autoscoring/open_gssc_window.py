import numpy as np
from PySide6.QtWidgets import (
    QMessageBox, QProgressDialog, QApplication,
)
from PySide6.QtCore import Qt, QTimer

try:
    from mne import create_info
    from .mne_raw import raw_array
    from gssc.infer import EEGInfer
    _GSSC_AVAILABLE = True
except ImportError:
    _GSSC_AVAILABLE = False

from widgets import GsscWindow
from .autoscore_results import apply_gssc
from scoring.write_scoring import write_scoring
from .staging_dialogs import ask_staging_options
from utilities.refresh_gui import refresh_gui


def open_gssc_window(ui):
    if not _GSSC_AVAILABLE:
        QMessageBox.information(
            None,
            "GSSC not installed",
            "GSSC is not installed. This feature requires running ScoringHero "
            "from source.\n\nInstall it with:\n\n    uv sync --extra gssc",
        )
        return

    channel_labels = [ch["Channel_name"] for ch in ui.config[1]]
    ui.GsscWindow = GsscWindow(channel_labels)
    ui.GsscWindow.settingsAccepted.connect(
        lambda settings: _after_gssc_settings(ui, settings)
    )
    ui.GsscWindow.show()


def _after_gssc_settings(ui, settings):
    options = ask_staging_options(ui, "GSSC")
    if options is None:
        return
    mode, overwrite_stages = options

    # Run GSSC with progress
    _run_gssc(ui, settings, mode, overwrite_stages)


if _GSSC_AVAILABLE:
    def _patched_loudest_vote(logits):
        """Reimplements gssc's loudest_vote and also captures per-epoch softmax probabilities."""
        import torch
        from torch.nn import NLLLoss, Softmax

        loss_func = NLLLoss(reduction="none")
        logits_t = torch.FloatTensor(np.array(logits))
        entrs = torch.zeros(logits_t.shape[:2])
        for idx in range(len(logits_t)):
            targs = torch.LongTensor(np.argmax(logits_t[idx].numpy(), axis=-1))
            entrs[idx] = loss_func(logits_t[idx], targs)
        min_inds = np.argmin(entrs.numpy(), axis=0)
        min_logits = logits_t[min_inds, np.arange(logits_t.shape[1])]
        out_infs = np.array(np.argmax(min_logits.numpy(), axis=1))

        # Compute softmax probabilities from the winning logits
        probs = Softmax(dim=-1)(min_logits).detach().numpy()
        _patched_loudest_vote._last_probs = probs  # shape [n_epochs, 5]

        return out_infs

    def _run_gssc(ui, settings, mode, overwrite_stages=None):
        progress = QProgressDialog("Running GSSC...", None, 0, 0)
        progress.setWindowTitle("Auto Score (GSSC)")
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.show()
        progress.raise_()
        QApplication.processEvents()
        QTimer.singleShot(0, lambda: _execute_gssc(ui, settings, mode, overwrite_stages, progress))

    def _execute_gssc(ui, settings, mode, overwrite_stages, progress):
        try:
            # Build MNE Raw from ui.eeg_data
            ch_names = [ch["Channel_name"] for ch in ui.config[1]]
            sfreq = ui.config[0]["Sampling_rate_hz"]
            info = create_info(ch_names=ch_names, sfreq=sfreq, ch_types="eeg")

            raw = raw_array(ui.eeg_data_display, info)

            # Run GSSC inference
            # PyTorch 2.6 changed the default of weights_only to True, but GSSC's
            # model files require weights_only=False to load. Patch torch.load
            # temporarily while EEGInfer loads its networks.
            import torch
            _orig_torch_load = torch.load
            def _torch_load_compat(*args, **kwargs):
                kwargs.setdefault("weights_only", False)
                return _orig_torch_load(*args, **kwargs)
            torch.load = _torch_load_compat
            try:
                eeginfer = EEGInfer(use_cuda=False)
            finally:
                torch.load = _orig_torch_load

            # Monkey-patch loudest_vote to capture per-epoch probabilities
            import gssc.infer as _gssc_infer_mod
            _orig_loudest_vote = _gssc_infer_mod.loudest_vote
            _gssc_infer_mod.loudest_vote = _patched_loudest_vote
            _patched_loudest_vote._last_probs = None
            try:
                gssc_stages, _ = eeginfer.mne_infer(
                    raw,
                    eeg=settings["eeg"],
                    eog=settings["eog"],
                    filter=settings["filter"],
                )
                probs = getattr(_patched_loudest_vote, "_last_probs", None)
            finally:
                _gssc_infer_mod.loudest_vote = _orig_loudest_vote

            channels_used = settings["eeg"] + settings["eog"]
            apply_gssc(ui.scoring, gssc_stages, probs, channels_used, mode, overwrite_stages)

            # Show "Finished"
            progress.setLabelText("Finished")
            QApplication.processEvents()

            write_scoring(ui)
            ui.HypnogramWidget.draw_hypnogram(ui)
            refresh_gui(ui)

            QTimer.singleShot(1500, progress.close)

        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            progress.close()
            QMessageBox.critical(
                None,
                "GSSC Error",
                f"An error occurred while running GSSC:\n\n"
                f"{type(e).__name__}: {e}\n\n"
                f"Traceback:\n{tb_str}",
            )
