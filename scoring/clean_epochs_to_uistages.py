def clean_epochs_to_uiscoring(ui, container_epochs):
    if ui.version[0] == 0 and ui.version[1] == 0:
        for epoch, stage in enumerate(ui.stages):
            stage["clean"] = 0 if any(epoch+1 in container for container in container_epochs) else 1

    else:
        if any(ui.this_epoch+1 in epoch for epoch in container_epochs):
            stage["clean"] = 0
        else:
            stage["clean"] = 1