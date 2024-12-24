def clean_epochs_to_uiscoring(ui, container):
    if container.key == 'A':
        for epoch, stage in enumerate(ui.stages):
            stage["clean"] = 0 if any(epoch+1 in container for container in container.epochs) else 1

        # Honestly not sure whether this is correct, but maybe it would be faster.
        # For sure the "stage" variable would need to be extracted first, something like ui.stages[something]
        # But I´m also not sure what happens when several epochs are labeled at once with artefacts. So rather
        # leave as is.    
        #if any(ui.this_epoch+1 in epoch for epoch in container.epochs):
        #    stage["clean"] = 0
        #else:
        #    stage["clean"] = 1