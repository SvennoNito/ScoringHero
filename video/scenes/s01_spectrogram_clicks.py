"""Scene 1: roam through the night and click several points in the spectrogram Panel."""

FRACTIONS = [0.12, 0.31, 0.55, 0.78, 0.94, 0.42]  # where in the night to click


def run(ctx):
    ctx.caption("Roam through the night: click the spectrogram to jump to any Epoch")
    ctx.state["s01_epochs"] = []
    spectrogram = ctx.ref("SpectogramWidget.graphics")
    ctx.move_cursor(ctx.center(spectrogram), 1.0)
    for fraction in FRACTIONS:
        epoch = int(fraction * ctx.ui.numepo)
        ctx.click(ctx.spectrogram_point(epoch), duration=0.9)
        ctx.state["s01_epochs"].append((epoch, ctx.ui.this_epoch))
        ctx.wait(0.6)


def check(ctx):
    clicks = ctx.state["s01_epochs"]
    assert len(clicks) == len(FRACTIONS), "not every spectrogram click ran"
    for epoch, displayed in clicks:
        assert displayed == epoch, f"click on epoch {epoch} displayed epoch {displayed}"
    assert len({displayed for _, displayed in clicks}) == len(FRACTIONS), "clicks did not change the Epoch"
    assert not any(ctx.ui.scoring.stage(i) for i in range(len(ctx.ui.scoring))), "Primary scoring is not empty"
