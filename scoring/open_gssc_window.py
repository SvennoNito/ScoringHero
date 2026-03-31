import numpy as np
from PySide6.QtWidgets import (
    QMessageBox, QProgressDialog, QApplication,
    QDialog, QVBoxLayout, QLabel, QCheckBox, QDialogButtonBox,
)
from PySide6.QtCore import Qt, QTimer

try:
    from mne import create_info
    from mne.io import RawArray
    from gssc.infer import EEGInfer
    _GSSC_AVAILABLE = True
except ImportError:
    _GSSC_AVAILABLE = False

from widgets import GsscWindow
from .write_scoring import write_scoring
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
    # Step A: Epoch length check
    epolen = ui.config[0]["Epoch_length_s"]
    if epolen != 30:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Epoch length mismatch")
        msg.setText(
            f"GSSC uses 30-second epochs, but your epoch length is {epolen}s.\n\n"
            "GSSC scores will be mapped onto your epoch grid automatically.\n\n"
            "You can adjust the epoch length in the Configuration panel "
            "if you prefer 30s epochs."
        )
        btn_continue = msg.addButton("Continue", QMessageBox.AcceptRole)
        msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec()
        if msg.clickedButton() != btn_continue:
            return

    # Step B: Existing scores check
    scored_count = sum(1 for e in ui.stages if e["stage"] is not None)
    mode = "overwrite"
    overwrite_stages = None

    if scored_count > 0:
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Existing scores detected")
        msg.setText(
            f"{scored_count} epoch(s) already have sleep scores.\n"
            "How would you like to proceed?"
        )
        btn_overwrite = msg.addButton("Overwrite all", QMessageBox.AcceptRole)
        btn_selective = msg.addButton("Overwrite selected stages...", QMessageBox.AcceptRole)
        btn_fill = msg.addButton("Fill missing only", QMessageBox.AcceptRole)
        msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec()

        clicked = msg.clickedButton()
        if clicked == btn_overwrite:
            mode = "overwrite"
        elif clicked == btn_selective:
            overwrite_stages = _ask_selective_stages()
            if overwrite_stages is None:
                return  # user cancelled or selected nothing
            mode = "selective"
        elif clicked == btn_fill:
            mode = "fill_missing"
        else:
            return

    # Step C: Run GSSC with progress
    _run_gssc(ui, settings, mode, overwrite_stages)


def _ask_selective_stages(parent=None):
    """Show dialog to select which existing stages to overwrite. Returns set or None."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Select stages to overwrite")
    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel("Overwrite epochs currently scored as:"))

    checkboxes = {}
    for stage in ["Wake", "N1", "N2", "N3", "REM"]:
        cb = QCheckBox(stage)
        checkboxes[stage] = cb
        layout.addWidget(cb)

    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)
    layout.addWidget(button_box)

    if dialog.exec() == QDialog.Accepted:
        selected = {s for s, cb in checkboxes.items() if cb.isChecked()}
        return selected if selected else None
    return None


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

            # Nuitka-compiled frames omit 'self' from f_locals, which crashes
            # MNE's _get_argvalues (frame introspection). Patch it to return
            # None instead — _init_kwargs is only used for repr, not inference.
            import mne.utils.misc as _mne_misc
            _orig_get_argvalues = _mne_misc._get_argvalues
            _mne_misc._get_argvalues = lambda: None
            try:
                raw = RawArray(ui.eeg_data, info, verbose=False)
            finally:
                _mne_misc._get_argvalues = _orig_get_argvalues

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

            # Stage mapping: GSSC int -> ScoringHero (stage, digit)
            stage_map = {
                0: ("Wake", 1),
                1: ("N1", -1),
                2: ("N2", -2),
                3: ("N3", -3),
                4: ("REM", 0),
            }

            channels_used = settings["eeg"] + settings["eog"]
            epolen = ui.config[0]["Epoch_length_s"]

            # Apply scores to ui.stages
            for i, epoch in enumerate(ui.stages):
                if mode == "fill_missing" and epoch["stage"] is not None:
                    continue
                if mode == "selective" and epoch["stage"] not in overwrite_stages:
                    continue

                # Find matching GSSC epoch
                if epolen == 30:
                    gssc_idx = i
                else:
                    # Map by midpoint: find which GSSC 30s epoch contains
                    # the midpoint of this ScoringHero epoch
                    midpoint = (epoch["start"] + epoch["end"]) / 2.0
                    gssc_idx = int(midpoint // 30)

                if gssc_idx < 0 or gssc_idx >= len(gssc_stages):
                    continue

                stage_int = int(gssc_stages[gssc_idx])
                stage_str, digit = stage_map[stage_int]
                epoch["stage"] = stage_str
                epoch["digit"] = digit
                epoch["source"] = "GSSC"
                epoch["channels"] = channels_used

                if probs is not None and gssc_idx < len(probs):
                    epoch["confidence"] = round(float(probs[gssc_idx, stage_int]), 4)
                else:
                    epoch["confidence"] = None

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
