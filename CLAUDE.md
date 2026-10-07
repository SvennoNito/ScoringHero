When reporting information to me, be extremely concise and sacrifice grammar for the sake of concision. When writing code, put simplicity first and avoid unnecessary frameworks.

Map: entry `scoringhero.py`; GUI `widgets/`; autoscorers (GSSC, NIDRA, YASA staging) `autoscoring/`; event detectors and their windows `event_detection/`; Scoring module and import/export `scoring/`; terms `GLOSSARY.md`; SUMO docs `docs/`; tests `tests/` (pytest, ruff; headless app fixture `loaded_ui` in `tests/conftest.py`; commit subject `[MOD|FIX|DOC|NEW]`; hook in `.githooks`, enable: `git config core.hooksPath .githooks`).
Python: always `uv run …` (`uv run pytest`, `uv run ruff`, `uv run python`); bare `python` is miniconda without project deps.
GitHub issues: `gh` CLI from bash (authed via GITHUB_TOKEN; eval kernel lacks the token), repo SvennoNito/ScoringHero. Windows; bash tool is unix-like.
