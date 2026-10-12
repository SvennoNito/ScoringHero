import numpy as np
from config.open_config_window import open_config_window

def test_wv(loaded_ui):
    ui = loaded_ui
    open_config_window(ui)
    shape = ui.TFWidget._cbar_img.image.shape
    wv = ui.WaveletPage
    lo = wv._power_min_spin.value()
    wv._power_max_spin.setValue(9.0); wv._power_max_spin.editingFinished.emit()
    ui.ConfigurationWindow.apply_pending()
    im = ui.TFWidget._cbar_img.image
    assert list(ui.TFWidget.img.levels) == [lo, 9] and im.shape == shape
    assert np.isclose(im.min(), lo) and np.isclose(im.max(), 9) and ui.TFWidget._cbar_max_label.toPlainText() == "9.0"

def test_sp(loaded_ui):
    ui = loaded_ui
    open_config_window(ui)
    shape = ui.SpectogramWidget._cbar_img.image.shape
    sp = ui.SpectrogramPage.spinboxes["Spectrogram_power_limits"]
    sp[1].setValue(7.0); sp[1].editingFinished.emit()
    ui.ConfigurationWindow.apply_pending()
    im = ui.SpectogramWidget._cbar_img.image
    assert list(ui.SpectogramWidget.img.levels) == [1, 7] and im.shape == shape
    assert np.isclose(im.max(), 7)
