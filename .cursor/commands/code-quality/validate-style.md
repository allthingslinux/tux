# Validate Style

## Overview

Validate a file (or files) you are working on against the Tux style guide. Run automated checks and manual review so the code is up to par with @core/style-guide.mdc.

Use this when you want to verify that a specific file conforms to project standards before committing or requesting review.

## Steps

1. **Identify Target File(s)**

   - Use the file(s) the user has open or explicitly specified (e.g. path in chat, "the file I'm working on").
   - If the user passed a path as a parameter (e.g. `/validate-style src/tux/foo.py`), use that path.
   - If no file is clear from context, ask: "Which file(s) should I validate?"

2. **Run Automated Checks on Target Path(s)**

   For each Python file to validate, run:

   - **Format check**: `uv run ruff format --check <path>`
   - **Lint**: `uv run ruff check <path>` (use `--fix` only if the user asked to fix issues)
   - **Type check**: `uv run basedpyright <path>`
   - **Docstrings**: `uv run pydoclint --config=pyproject.toml <path>`

   Replace `<path>` with the actual file path (e.g. `src/tux/services/foo.py`). For multiple files, run each tool once with all paths.

3. **Report Tool Output**

   - Summarize results: which checks passed, which failed.
   - For failures, quote or paraphrase the tool output and point to the relevant lines.
   - Do not fix code unless the user asked you to fix issues; focus on validation and reporting.

4. **Manual Style-Guide Review**

   Using @core/style-guide.mdc, spot-check patterns that tools may not fully enforce:

   - **Naming**: `snake_case` (functions/vars), `PascalCase` (classes), `UPPER_SNAKE_CASE` (constants).
   - **Type hints**: `Type | None` (not `Optional[Type]`); `dict[str, int]`, `list[str]`; params/returns annotated.
   - **Comparisons**: `if attr:`, `if attr is None:` — not `== True`, `== False`, or `== None`.
   - **Imports**: Three groups (stdlib → third-party → local), alphabetical within each, blank lines between.
   - **File length**: File under 1600 lines.
   - **Docstrings**: NumPy-style for public APIs; `__init__` documented in class docstring.
   - **Idioms**: Comprehensions over loop+append; `with` for file ops; `pathlib` over `os.path`; no `print()` (use loguru).

   Note any violations with file/line references when possible.

5. **Summarize and Recommend**

   - **Pass**: All automated checks pass and no notable style-guide violations → report "File is up to par with the style guide."
   - **Fail**: List failed checks and manual findings. Suggest concrete fixes (e.g. "Use `Type | None` here") and link to the style guide where relevant.

## Error Handling

- If a tool fails (e.g. ruff, basedpyright, pydoclint exits non‑zero): report the failure and the tool output; do not claim the file passes.
- If the path is invalid or not a Python file: say so and ask for a valid `.py` path.
- If the user wants auto-fixes: run `uv run ruff check --fix <path>` and `uv run ruff format <path>`, then re-run validation.

## Validation Checklist

- [ ] Identified the correct file(s) to validate
- [ ] Ran `uv run ruff format --check <path>`
- [ ] Ran `uv run ruff check <path>` (and `--fix` if user requested fixes)
- [ ] Ran `uv run basedpyright <path>`
- [ ] Ran `uv run pydoclint --config=pyproject.toml <path>`
- [ ] Checked naming, type hints, comparisons, imports per style guide
- [ ] Verified file under 1600 lines
- [ ] Verified NumPy docstrings for public APIs
- [ ] Reported pass/fail and any violations with concrete suggestions

## See Also

- Related command: `/lint` - Lint and fix project-wide
- Related command: `/refactor` - Refactor for patterns and DRY
- Related command: `/deslop` - Write high-quality code (research-first)
- Related rule: @core/style-guide.mdc - Style guide reference
