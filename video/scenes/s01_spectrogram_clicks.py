"""Scene 1: roam through the night and click several points in the spectrogram Panel."""

FRACTIONS = [0.12, 0.31, 0.55, 0.78, 0.94, 0.42]  # where in the night to click


def run(ctx):
    ctx.caption("Roam through the night: click the spectrogram to jump to any Epoch")
    ctx.state["s01_epochs"] = []
    spectrogram = ctx.ref("SpectogramWidget.graphics")
    ctx.move_cursor(ctx.center(spectrogram), 1.0)
    for fraction in FRACTIONS:
        epoch = int(fraction * ctx.ui.numepo)
        ctx.click_epoch(epoch)
        ctx.state["s01_epochs"].append(epoch)
        ctx.wait(0.6)


def check(ctx):
    assert len(set(ctx.state["s01_epochs"])) == len(FRACTIONS), "not every spectrogram click ran or the Epoch did not change"
    assert not any(ctx.ui.scoring.stage(i) for i in range(len(ctx.ui.scoring))), "Primary scoring is not empty"
