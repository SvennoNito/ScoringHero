def clean_epochs_to_uiscoring(ui, container):
    """Mark epochs covered by an artefact event unclean, all others clean."""
    if container.key == 'A':
        n = len(ui.scoring)
        # epochs_set holds 1-based epoch numbers
        artefact = {epoch - 1 for epoch_set in container.epochs_set for epoch in epoch_set if 1 <= epoch <= n}
        ui.scoring.set_clean(range(n), 1)
        ui.scoring.set_clean(artefact, 0)
