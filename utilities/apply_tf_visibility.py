def apply_tf_visibility(ui):
    """Show or hide the TF panel and resize the EEG signal panel accordingly.

    When visible:   EEG occupies rows 10-77 (68 rows), TF occupies rows 78-94.
    When hidden:    EEG expands to rows 10-94 (85 rows), TF widget is hidden.
    """
    visible = ui.config[0].get("Wavelet_panel_visible", True)
    if visible:
        ui.TFWidget.graphics.show()
        ui.central_layout.addWidget(ui.SignalWidget.axes, 10, 0, 68, 101)
        ui.central_layout.addWidget(ui.PaintEventWidget, 10, 0, 68, 101)
        ui.SignalWidget.axes.getAxis("bottom").setStyle(showValues=False)
    else:
        ui.TFWidget.graphics.hide()
        ui.central_layout.addWidget(ui.SignalWidget.axes, 10, 0, 85, 101)
        ui.central_layout.addWidget(ui.PaintEventWidget, 10, 0, 85, 101)
        ui.SignalWidget.axes.getAxis("bottom").setStyle(showValues=True)
