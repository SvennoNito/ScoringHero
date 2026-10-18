"""Scene 13: remove the Comparison scoring again."""


def run(ctx):
    ctx.wait_idle()
    ctx.caption("Remove the Comparison scoring again")
    ctx.click_menu("action_remove_comparison")
    ctx.wait(1.5)
    ctx.caption(None)


def check(ctx):
    ui = ctx.ui
    assert ui.scoring_comparison is None, "Comparison scoring was not removed"
    assert not ui.action_comparison_stats.isEnabled(), "comparison statistics still enabled"
