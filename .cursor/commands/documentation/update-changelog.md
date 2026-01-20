# Update Changelog

## Overview

Update the `[Unreleased]` section of `CHANGELOG.md` from recent commits. This command reviews pending commits, maps them to Keep a Changelog categories (Added, Changed, Fixed, etc.) using conventional commit types, and merges new entries into the Unreleased section without duplicating existing content.

## Steps

1. **Gather Pending Commits**
   - Run `git log --oneline -15` (or use a different count if the user provides one in the command parameters)
   - Optionally: `git log --oneline v0.1.0..HEAD` or `git log --oneline <last-tag>..HEAD` to include only commits since the latest release
   - For each commit, note: **subject** (and optionally **body** via `git log -15 --format="%s%n%b---"`)

2. **Map Commits to Keep a Changelog Categories**
   - **feat** → **Added** (new features, capabilities)
   - **fix** → **Fixed** (bug fixes)
   - **refactor**, **perf**, **style** → **Changed** (improvements, no new behavior or bug fix)
   - **docs** → **Changed** (or **Added** if it’s net-new user-facing docs; usually **Changed**)
   - **deprecate** or `!` breaking in scope → **Deprecated** or **Removed** as appropriate
   - **security** or `fix(security)` → **Security**
   - **chore**, **ci**, **build**, **test** → Omit from user-facing changelog unless notable (e.g. a new `uv run` script)

3. **Parse Conventional Format**
   - Use pattern: `type(scope): description` or `type: description`
   - **scope** (e.g. `jail`, `remindme`, `cog_loader`) can be used as a **Group** in bullets: `* **scope** (or human name): description`
   - **description**: first line, sentence case, no period at end; use for the main bullet text
   - If the commit body adds important detail, fold it into the bullet or a sub-bullet

4. **Preserve Existing Unreleased Content**
   - Read the current `## [Unreleased]` block in `CHANGELOG.md`
   - Do **not** remove or rephrase existing bullets
   - Only **append** new entries that are not already covered (same change or same scope+idea)
   - When in doubt, prefer one combined bullet (e.g. one **cog_loader** item) over many tiny bullets

5. **Apply Project Changelog Style**
   - Sections: `### Added`, `### Changed`, `### Fixed`, `### Deprecated`, `### Removed`, `### Security` (only include sections that have entries)
   - Bullets: `* **Group**: Summary.` with optional sub-bullets indented 4 spaces: `* Detail.`
   - **Group** = scope or a short human-readable feature area (e.g. `Jail system`, `Time conversion`, `Cog loader`)
   - Collapse related commits into single bullets where it makes sense (e.g. multiple `fix(on_ready)` → one `**on_ready handlers**` with sub-bullets)
   - Match tone: past tense or passive where the existing changelog uses it; otherwise present or past as fits

6. **Merge and Write**
   - Insert new bullets under the correct `###` heading
   - Group by **Group** when there are several bullets in one section (optional; follow existing layout)
   - Keep `## [Unreleased]` immediately above `## [x.y.z]`; do not add extra blank lines between the end of Unreleased and the next version header
   - Leave the `<!-- markdownlint-disable MD024 MD007 -->` and the initial `# Changelog` / format notes at the top unchanged

7. **Sanity-Check**
   - Ensure no duplicate entries for the same change
   - Ensure all new bullets are under the correct `###` (Added/Changed/Fixed/etc.)
   - Ensure format matches the rest of the file (asterisks, spacing, no stray headers)

## Error Handling

- **No commits / empty range**: Do not clear `[Unreleased]`; only add when there are new commits to document.
- **Non‑conventional subject**: Map by best effort (e.g. “Add X” → Added; “Fix Y” → Fixed) or group under **Changed** if unclear.
- **Merge commits**: Skip or use only the first-line subject; avoid duplicate bullets from the same logical change.

## Checklist

- [ ] Pending commits reviewed (`git log --oneline -15` or user-specified range)
- [ ] Each commit mapped to Added / Changed / Fixed / Deprecated / Removed / Security
- [ ] Existing `[Unreleased]` content left intact
- [ ] New entries appended without duplicating existing bullets
- [ ] Format matches project style (`* **Group**: …` and optional sub-bullets)
- [ ] No extra sections or headers; `[Unreleased]` remains directly above the latest version

## See Also

- Related command: `/update-docs` - Update docs for code changes
- Related command: `/validate-docs` - Audit documentation
- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [Conventional Commits](https://www.conventionalcommits.org/) — `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`
- `CHANGELOG.md` in the project root

## Additional Notes

- **Scope**: Prefer `[Unreleased]` only; no need to create new version headers unless the user asks.
- **Omit**: `chore`, `ci`, `build`, `test` unless they are user- or contributor-visible (e.g. new CLI, new script).
- **Consolidation**: Prefer fewer, clearer bullets (e.g. one “on_ready handlers” with sub-bullets) over one bullet per commit when they describe the same area.
