# Deslop Documentation

## Overview

Produce high-quality documentation following strict Tux project standards, avoiding AI-generated pitfalls. This command guides you through writing consistent, accurate, and maintainable documentation free of "slop" - unnecessary complexity, inconsistencies, inaccuracies, and anti-patterns.

## Steps

1. **Research-First Protocol (MANDATORY)**
   - Read relevant code - Verify documentation matches actual implementation. Don't document what you think exists - verify it.
   - Check existing documentation - Search for similar content, check for duplication, understand existing patterns
   - Verify configuration - Compare documentation examples against actual config files (`config/*.example`, `compose.yaml`)
   - Test code examples - Run all code snippets and commands to ensure they work
   - Check API references - Verify CLI commands, environment variables, and API endpoints exist
   - Map documentation structure - Understand where content belongs (user/admin/developer/selfhost/reference)
   - Verify understanding - Explain what you're documenting, why it's needed, who the audience is
   - Check for blockers - Ambiguous requirements? Missing information? Outdated codebase references?

2. **Write Consistent Documentation**
   - Match existing style - Use the same formatting, tone, and structure as similar documentation
   - Follow established patterns - Use existing command documentation patterns, configuration examples, feature documentation styles
   - Reuse existing content - Don't duplicate - reference related documentation instead of repeating information
   - Stay in scope - ONLY document what's requested. Do NOT add unrelated improvements or extra features
   - Preserve patterns - If you see a pattern (e.g., command syntax format, admonition usage), maintain it exactly
   - Use existing examples - Check for existing code/config examples before creating new ones

3. **Follow Documentation Standards**
   - Diátaxis framework: Choose the right type (tutorial/how-to/reference/explanation) - see @docs/principals.mdc
   - Writing style: Active voice, second person ("you"), present simple tense, imperative verbs - see @docs/style.mdc
   - Zensical syntax: Use appropriate features (admonitions, tabs, code blocks, diagrams) - see @docs/syntax.mdc
   - Structure: Follow navigation patterns, use index pages, proper heading hierarchy - see @docs/structure.mdc
   - Formatting: Sentence case titles, proper code formatting, consistent list styles - see @docs/style.mdc
   - Patterns: Follow established documentation patterns for commands, features, configuration - see @docs/patterns.mdc

4. **Accuracy Standards**
   - Code examples: ALL code snippets must work when copied directly
   - CLI commands: Verify commands exist and syntax is correct (`uv run db health`, not `python db.py health`)
   - Configuration: Match examples against actual config files and environment variables
   - API references: Verify endpoints, parameters, and responses match implementation
   - Default values: Check actual defaults in code, not assumed values
   - Environment variables: Verify variable names match actual usage in codebase
   - Database schema: Document actual models and relationships, not assumptions
   - Permission levels: Verify actual permission requirements, not assumptions

5. **Cross-Reference Standards**
   - Internal links: Use relative paths (`../manage/database.md`), verify links work
   - Navigation: Update `zensical.toml` nav array if adding new pages
   - Related content: Link to related documentation sections appropriately
   - External links: Verify external URLs are valid and appropriate
   - Code references: Link to actual source files when relevant
   - Avoid broken links: Test all links before submitting

6. **Content Quality Standards**
   - User-first: Address real user needs, not just system capabilities
   - Practical: Include working examples and real-world configurations
   - Comprehensive: Cover all likely user questions and edge cases
   - Accessible: Use clear language, avoid jargon, provide context
   - Scannable: Use proper headings, lists, and formatting for quick scanning
   - Complete: Include prerequisites, step-by-step instructions, next steps

7. **Review Before Submitting**
   - Verify accuracy - Test all code examples, verify all commands work, check all configuration examples
   - Check consistency - Ensure documentation matches style and patterns of similar files
   - Review scope - Verify you only documented what was requested - no extra "improvements"
   - Check for slop - Review documentation against anti-patterns (see Error Handling section)
   - Remove placeholder text - Ensure no `TODO`, `FIXME`, placeholder content, or incomplete sections
   - Verify patterns - Ensure you didn't break established documentation patterns or conventions
   - Verify examples - Run code examples, test commands, verify configuration works
   - Check cross-references - Verify all links work, navigation is updated if needed
   - Build verification - Ensure documentation builds without errors (`uv run docs build`)

8. **Mandatory Self-Audit**
   - Test all code examples and commands
   - Verify documentation builds successfully
   - Check cross-references and links
   - Verify accuracy against codebase
   - Compare with similar documentation for consistency
   - Provide evidence (build output, code references, verification steps)
   - Use status markers: ✅ (completed), ⚠️ (recoverable issue fixed), 🚧 (blocked after exhausting research)

## Error Handling

### Common Anti-Patterns to Avoid

**Documentation Anti-Patterns:**

- Passive voice - ALWAYS use active voice ("You configure X" not "X is configured")
- Present continuous tense - Use present simple ("You use X" not "You are using X")
- Generic examples - Use specific, realistic examples that users can actually use
- Outdated information - ALWAYS verify against current codebase, never assume
- Missing context - Include prerequisites, next steps, and related resources
- Broken links - Verify all internal and external links work
- Inconsistent formatting - Match existing documentation style exactly
- Wrong documentation type - Use appropriate Diátaxis type (tutorial/how-to/reference/explanation)
- Missing code language - ALWAYS specify language in code fences (```bash,```python, ```env)
- Placeholder text - Remove all `TODO`, `FIXME`, `PLACEHOLDER`, incomplete sections
- Assumed defaults - Verify actual default values in code/config, don't assume
- Wrong command syntax - Verify CLI commands exist and syntax matches actual implementation
- Inconsistent terminology - Use established terminology from codebase and existing docs
- Missing examples - Include practical, working examples for all features/configurations
- Over-complex explanations - Keep explanations simple and direct, avoid unnecessary complexity
- Missing prerequisites - List requirements and prerequisites before technical content
- No next steps - End with suggested next steps and related resources

**AI Documentation Slop Detection:**

- Extra admonitions inconsistent with file style (overuse of warnings/tips/notes)
- Over-explanatory: Unnecessary background that doesn't help users
- Pattern violations: Not following established documentation patterns, breaking conventions
- Generic & vague content: Empty AI-words ("robust", "seamless", "efficient"), generic descriptions
- Duplication: Repeating information that exists elsewhere instead of referencing
- Inconsistent formatting: Not matching existing documentation style (heading levels, list styles, code formatting)
- Debug artifacts: Placeholder text, incomplete sections, `TODO` comments
- Scope creep: Adding documentation for features/options not requested
- Inaccurate examples: Code/config examples that don't match actual implementation
- Missing verification: Documentation that wasn't tested against actual codebase

If you encounter any of these patterns:

- Remove them immediately
- Replace with proper patterns from existing documentation
- Verify the fix doesn't introduce inaccuracies
- Test all examples and verify against codebase

## Checklist

- [ ] Read and understood the entire file being edited
- [ ] Checked similar documentation files to understand existing patterns
- [ ] Searched for existing documentation - found similar content and referenced/expanded it
- [ ] Verified accuracy - tested code examples, verified commands, checked configuration
- [ ] Matched existing formatting and style exactly
- [ ] Followed documentation structure patterns (headings, lists, code blocks)
- [ ] Used appropriate Diátaxis type (tutorial/how-to/reference/explanation)
- [ ] Applied writing standards (active voice, second person, present simple tense)
- [ ] Used correct Zensical syntax (admonitions, code blocks, formatting)
- [ ] Verified all code examples work when copied directly
- [ ] Tested all CLI commands and verified syntax is correct
- [ ] Compared configuration examples against actual config files
- [ ] Verified environment variables match actual usage in codebase
- [ ] Checked all cross-references and links work
- [ ] Updated navigation in `zensical.toml` if adding new pages
- [ ] No placeholder text, `TODO`, or incomplete sections
- [ ] No broken links (internal or external)
- [ ] Documentation builds successfully (`uv run docs build`)
- [ ] Only requested changes were made (no scope creep)
- [ ] No unrelated documentation was modified
- [ ] Established patterns were preserved exactly
- [ ] All examples verified against actual codebase/implementation
- [ ] Included prerequisites and next steps where appropriate
- [ ] Used consistent terminology from codebase and existing docs
- [ ] Applied appropriate admonitions (tip/warning/note/danger)
- [ ] Code blocks have language specifiers (```bash,```python, ```env)
- [ ] Adversarial verification - tested edge cases, verified defaults, checked actual behavior

## See Also

- Related command: `/update-docs` - Update documentation for code changes
- Related command: `/generate-docs` - Generate API documentation
- Related command: `/docs-serve` - Start local documentation server
- Related rule: @docs/docs.mdc - Documentation standards master guide
- Related rule: @docs/style.mdc - Writing style and formatting
- Related rule: @docs/patterns.mdc - Documentation patterns and examples
- Related rule: @docs/principals.mdc - Diátaxis framework principles
- Related rule: @docs/syntax.mdc - Zensical syntax reference
- Related rule: @docs/structure.mdc - Documentation organization
