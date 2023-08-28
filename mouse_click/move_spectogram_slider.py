def move_spectogram_slider(slider_value, ui):
    ui.SpectogramWidget.adjust_color_limit(ui.power, slider_value)
