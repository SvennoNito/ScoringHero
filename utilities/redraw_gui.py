from annotations.draw_box_in_epoch import draw_box_in_epoch

def redraw_gui(ui):

    # Redraw EEG data
    ui.SignalWidget.draw_signal(ui.config, ui.eeg_data, ui.times, ui.this_epoch)

    # Update display text
    ui.DisplayedEpochWidget.update_text(ui.this_epoch, ui.numepo, ui.stages)    

    # Draw annotations
    for container in ui.AnnotationContainer:
        draw_box_in_epoch(ui, container)    
