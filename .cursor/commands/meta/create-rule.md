# Create Cursor Rule

## Overview

Create a new Cursor rule following Tux project standards. This command guides you through selecting a domain, determining rule type, generating the rule file from the template, and validating it.

## Steps

1. **Choose Domain**
   - Review available domains in `.cursor/rules/`
   - Select appropriate domain directory:
     - `core/` - Core project rules (tech stack, dependencies)
     - `database/` - Database patterns (models, migrations, controllers, services, queries)
     - `modules/` - Discord bot modules (cogs, commands, events, permissions, interactions)
     - `testing/` - Testing patterns (pytest, fixtures, markers, coverage, async)
     - `docs/` - Documentation rules (Zensical, writing standards, structure)
     - `security/` - Security patterns (secrets, validation, dependencies)
     - `error-handling/` - Error handling (patterns, logging, Sentry, user feedback)
     - `ui/` - UI components (Discord Components V2)
     - `meta/` - System documentation (specifications)
   - If domain doesn't exist, create the directory first

2. **Determine Rule Type**
   - **Always-Apply Rule**: Project-wide standards that should apply to every chat
     - Use `alwaysApply: true`
     - No `globs` needed
     - Example: Core coding standards, project structure
   - **Intelligent Rule**: AI-selected based on context and description
     - Use `alwaysApply: false` with `description` field (60-120 chars)
     - Include domain keywords in description
     - No `globs` needed
     - Example: Database patterns, testing patterns
   - **File-Scoped Rule**: Applies when editing matching files
     - Use `alwaysApply: false` with `globs` patterns
     - Comma-separated glob patterns (no quotes, no brackets)
     - Example: `src/tux/database/**/*.py, tests/database/**/*.py`
   - **Manual Rule**: Invoked via @-mention only
     - Use `alwaysApply: false`
     - No `globs`, no `description`
     - Example: Code generation templates

3. **Create Rule File**
   - Navigate to appropriate domain directory: `.cursor/rules/{domain}/`
   - Create new `.mdc` file with kebab-case name
   - Example: `database/models.mdc`, `modules/commands.mdc`
   - Copy template from `.cursor/templates/rule-template.mdc`
   - Fill in frontmatter:

     ```yaml
     ---
     description: Brief description (60-120 chars) with domain keywords
     globs: optional/file/pattern, another/pattern  # Only for file-scoped rules
     alwaysApply: false  # true for always-apply rules
     ---
     ```

   - **Important**: `globs` must be comma-separated, no quotes, no brackets
   - Example: `globs: src/tux/database/**/*.py, tests/database/**/*.py`
   - NOT: `globs: ["src/tux/database/**/*.py"]` or `globs: "pattern"`

4. **Write Rule Content**
   - Add clear title (H1)
   - Write Overview section explaining purpose and scope
   - Add Patterns section with ✅ GOOD / ❌ BAD examples
   - Include code examples in code blocks
   - Add Best Practices section
   - Add Anti-Patterns section
   - Include Examples section (optional, for detailed use cases)
   - Add See Also section with cross-references:
     - Related rules: `@domain/rule-name.mdc`
     - Related commands: `/command-name`
     - General standards: `@AGENTS.md`
     - Rules catalog: `@.cursor/rules/rules.mdc`

5. **Validate Rule**
   - Run validation: `uv run ai validate-rules`
   - Check for errors:
     - Frontmatter format (must start with `---`)
     - Description length (60-120 chars for intelligent rules)
     - Globs format (comma-separated, no quotes/brackets)
     - Content requirements (title, patterns, examples)
     - File size (max 500 lines, except for exceptions)
   - Fix any validation errors

6. **Update Rules Catalog** (Optional)
   - If rule is new domain or significant addition, update `.cursor/rules/rules.mdc`
   - Add entry to appropriate section
   - Format: `` `domain/rule-name.mdc` - Brief description ``

7. **Test Rule**
   - Test rule by @-mentioning it in Cursor chat
   - Verify rule applies correctly
   - Check that examples are accurate
   - Ensure cross-references work

## Error Handling

If validation fails:

- **Frontmatter errors**: Check YAML format, ensure `---` delimiters are correct
- **Description errors**: Ensure 60-120 chars, include domain keywords
- **Globs errors**: Use comma-separated format, no quotes, no brackets
- **Content errors**: Ensure title (H1), patterns with ✅/❌, code examples
- **Size errors**: Split rule if over 500 lines (except for exceptions)

If rule doesn't apply:

- **Always-apply rule**: Check `alwaysApply: true` is set correctly
- **Intelligent rule**: Ensure `description` includes relevant keywords
- **File-scoped rule**: Verify `globs` patterns match target files
- **Manual rule**: Use @-mention to invoke

## Checklist

- [ ] Domain directory selected or created
- [ ] Rule type determined (always-apply, intelligent, file-scoped, manual)
- [ ] Rule file created with kebab-case name
- [ ] Frontmatter filled correctly (description, globs if needed, alwaysApply)
- [ ] Title (H1) added
- [ ] Overview section written
- [ ] Patterns section with ✅ GOOD / ❌ BAD examples included
- [ ] Code examples included in code blocks
- [ ] Best Practices section added
- [ ] Anti-Patterns section added
- [ ] See Also section with cross-references added
- [ ] Rule validated (`uv run ai validate-rules`)
- [ ] All validation errors fixed
- [ ] Rules catalog updated (if needed)
- [ ] Rule tested via @-mention

## Examples

### Creating a Database Rule

1. Domain: `database/`
2. File: `database/models.mdc`
3. Type: Intelligent (with description)
4. Frontmatter:

   ```yaml
   ---
   description: SQLModel database model patterns for Tux
   alwaysApply: false
   ---
   ```

5. Content: Add patterns, examples, anti-patterns
6. Validate: `uv run ai validate-rules`

### Creating a File-Scoped Rule

1. Domain: `testing/`
2. File: `testing/pytest.mdc`
3. Type: File-scoped
4. Frontmatter:

   ```yaml
   ---
   description: Pytest configuration and patterns for Tux
   globs: tests/**/*.py, src/tux/**/test_*.py
   alwaysApply: false
   ---
   ```

5. Content: Add patterns, examples, anti-patterns
6. Validate: `uv run ai validate-rules`

### Creating an Always-Apply Rule

1. Domain: `core/`
2. File: `core/tech-stack.mdc`
3. Type: Always-apply
4. Frontmatter:

   ```yaml
   ---
   alwaysApply: true
   ---
   ```

5. Content: Add patterns, examples, anti-patterns
6. Validate: `uv run ai validate-rules`

## See Also

- Related rule: @meta/cursor-rules.mdc - Rules specification
- Related rule: @.cursor/rules/rules.mdc - Complete catalog of all rules
- Related guide: [Creating Cursor Rules Guide](../../../docs/content/developer/guides/creating-cursor-rules.md)
- Related command: `/validate-rules` - Validate all rules and commands
- Related template: @.cursor/templates/rule-template.mdc - Rule template

## Additional Notes

- **Naming**: Use kebab-case for rule filenames (e.g., `database-models.mdc`)
- **Size**: Keep rules under 500 lines (exceptions: specs, large references)
- **Specificity**: Make rules project-specific, not generic programming advice
- **Examples**: Always include working code examples
- **Cross-references**: Link to related rules and commands for context
- **Maintenance**: Update rules when project patterns change
