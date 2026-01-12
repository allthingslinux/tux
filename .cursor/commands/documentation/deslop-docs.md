# Deslop Docs

## Overview

Produce high-quality documentation following strict Tux project standards, avoiding AI-generated pitfalls. This command guides you through writing consistent, maintainable documentation free of "slop" - unnecessary complexity, inconsistencies, and anti-patterns.

## Steps

1. **Research-First Protocol (MANDATORY)**
   - Read relevant documentation rules - Review all documentation rules in `.cursor/rules/docs/` to understand standards
   - **Check documentation templates** - Review templates in `docs/content/reference/docs/templates/` for the type of documentation you're creating:
     - Use `command-template.md` for individual commands
     - Use `command-group-template.md` for command groups with subcommands
     - Use `module-template.md` for module overviews
     - Use `feature-template.md` for automated features and systems
   - Read existing documentation - Study similar pages in `docs/content/` to match style and structure
   - Map documentation structure:
     - Content Organization: Directory structure, navigation hierarchy, content types (tutorial/how-to/reference/explanation)
     - Navigation Configuration: Review `zensical.toml` nav array, understand explicit navigation requirements
     - Existing Patterns: Search for similar documentation - leverage or expand existing content instead of creating new
     - Cross-References: Identify related pages, ensure proper linking
   - Inspect existing docs - Study implementations before writing. If leveraging existing content, trace all references first
   - Verify understanding - Explain documentation flow, structure, navigation, impact. Use structured thinking for complex topics
   - Check for blockers - Ambiguous requirements? Missing context? Multiple valid organizational choices? Missing critical information?

2. **Write Consistent Documentation**
   - **Follow template structure** - When creating new documentation, use the appropriate template from `docs/content/reference/docs/templates/` as a starting point. Fill in all sections and remove optional sections that don't apply
   - Match existing style - Use the same writing style, formatting, and structure as similar pages
   - Follow established patterns - If commands are documented in a specific format, use that format. If configs use tabs, use tabs
   - Reuse existing content - Don't duplicate - check if similar documentation exists that can be expanded or referenced
   - Stay in scope - ONLY modify what's requested. Do NOT change unrelated documentation
   - Preserve patterns - If you see a pattern (e.g., specific admonition types, code block styles), maintain it exactly
   - Use existing examples - Check for existing code/config examples before creating new ones

3. **Follow Documentation Standards**
   - Writing style: ALWAYS use active voice, second person ("you"), present simple tense, imperative verbs
   - Formatting: Use sentence case for headings, proper heading hierarchy (H1→H2→H3), complete sentences in lists
   - Code blocks: ALWAYS include language specifier, introduce with brief description ending with colon
   - Placeholders: Use `<PLACEHOLDER_NAME>` format, explain each placeholder
   - Links: Use descriptive link text, NEVER "click here" or "see this page"
   - Images: Include descriptive alt text without "Image of..." prefix

4. **Zensical Syntax Standards**
   - Admonitions: Use appropriate types (`note`, `warning`, `tip`, etc.), proper syntax with `!!!` or `???`
   - Code blocks: Triple backticks with language specifier, introduce purpose before block
   - Code blocks: Distinguish command from output, use appropriate language specifiers
   - Tabs: Use content tabs for alternatives (e.g., different config formats)
   - Diagrams: Use Mermaid.js for flowcharts, sequence diagrams, etc. when appropriate
   - Annotations: Use sparingly for important clarifications, follow proper syntax
   - Icons: Use appropriate icon shortcodes when helpful, don't overuse

5. **Content Organization Standards**
   - Content type: Determine if tutorial/how-to/reference/explanation per Diátaxis framework
   - Location: Place in correct directory (`user/`, `admin/`, `developer/`, `reference/`, `selfhost/`, `community/`)
   - Navigation: Update `zensical.toml` nav array if adding new pages or sections
   - Structure: Follow article goals → prerequisites → content → next steps pattern
   - Index pages: Use `index.md` files for section overviews and navigation

6. **Technical Content Standards**
   - Accuracy: Verify all commands, code examples, and configurations against actual implementation
   - Examples: Include working examples, not just theory
   - Configuration: Show actual config files with placeholders, explain each option
   - Commands: Introduce purpose, distinguish command from output
   - API documentation: Specify HTTP methods, use backticks for paths and parameters
   - Path parameters: Use `{parameter}` format in URLs

7. **Review Before Submitting**
   - Verify accuracy - Check that all commands, code, and configurations actually work
   - Check consistency - Ensure your documentation matches the style and patterns of similar pages
   - Review scope - Verify you only changed what was requested - no extra "improvements"
   - Check for slop - Review your documentation against anti-patterns (see Error Handling section)
   - Remove debug content - Ensure no placeholder text, incomplete sections, or test content remains
   - Verify patterns - Ensure you didn't break established patterns or conventions
   - Verify navigation - Check that navigation is updated if needed, links work correctly
   - Adversarial verification - Actively try to falsify assumptions. Look for broken links, missing context, unclear instructions

8. **Mandatory Self-Audit**
   - Verify navigation - Check `zensical.toml` nav array is updated if needed
   - Test links - Verify all internal and external links work
   - Verify structure - Check heading hierarchy, formatting, code blocks render correctly
   - Check for regressions - Ensure no broken cross-references or missing context
   - Verify all changes match requested scope
   - Provide evidence (link checks, structure verification, navigation review)
   - Use status markers: ✅ (completed), ⚠️ (recoverable issue fixed), 🚧 (blocked after exhausting research)

## Error Handling

### Common Anti-Patterns to Avoid

**Documentation Anti-Patterns:**

- Passive voice - ALWAYS use active voice ("You can configure..." not "Configuration can be done...")
- Vague language - Use specific, actionable instructions, NEVER generic phrases
- Missing context - ALWAYS provide prerequisites and clear introductions
- Broken links - Verify all links work, use descriptive link text
- Inconsistent formatting - Match existing style exactly (sentence case, list style, code block format)
- Missing examples - Include working code/config examples, not just descriptions
- Generic admonitions - Use specific types (`warning`, `tip`, `note`) appropriately
- Over-formatting - Don't use bold/italics excessively, follow existing patterns
- Missing navigation - Update `zensical.toml` nav array when adding new pages
- Incomplete instructions - Every step should be actionable and complete

**AI Documentation Slop Detection:**

- Extra formatting inconsistent with file style
- Over-explanatory content: unnecessary background, excessive context
- Type system abuse: Using complex syntax when simple works
- Content organization issues: Over-engineering structure, duplicating existing content, breaking existing patterns
- Consistency violations: Inconsistent terminology, not following file structure, magic values in examples
- Debug artifacts: Placeholder text, incomplete sections, test content in production docs
- Pattern violations: Not following existing patterns, breaking conventions, adding features not requested
- Generic & vague content: Empty AI-words ("robust", "seamless", "efficient"), generic descriptions without specifics

If you encounter any of these patterns:

- Remove them immediately
- Replace with proper patterns from the codebase
- Verify the fix doesn't break existing functionality or navigation

## Checklist

- [ ] Read and understood all relevant documentation rules
- [ ] Reviewed appropriate documentation template from `docs/content/reference/docs/templates/` (command, command-group, module, or feature)
- [ ] Checked similar documentation pages to understand existing patterns
- [ ] Searched for existing content - found similar documentation and leveraged/expanded it
- [ ] Traced references - verified changes won't break cross-references
- [ ] Matched existing writing style exactly (active voice, second person, present tense)
- [ ] Followed existing formatting style and organization
- [ ] Used existing examples/patterns instead of creating new ones
- [ ] All links verified and working (internal and external)
- [ ] Navigation updated in `zensical.toml` if adding new pages
- [ ] No placeholder text or incomplete sections
- [ ] All code examples tested and accurate
- [ ] All commands verified against actual implementation
- [ ] Proper heading hierarchy (H1→H2→H3)
- [ ] Sentence case for headings
- [ ] Descriptive link text (no "click here")
- [ ] Alt text for images (without "Image of..." prefix)
- [ ] Appropriate admonition types used correctly
- [ ] Code blocks have language specifiers and introductions
- [ ] Placeholders explained (`<PLACEHOLDER_NAME>` format)
- [ ] Content type appropriate (tutorial/how-to/reference/explanation)
- [ ] Location correct (`user/`, `admin/`, `developer/`, etc.)
- [ ] Article structure follows pattern (goals → prerequisites → content → next steps)
- [ ] Only requested changes were made (no scope creep)
- [ ] No unrelated documentation was modified
- [ ] Established patterns were preserved exactly
- [ ] All technical content verified against actual codebase
- [ ] Verified against usage - checked what users actually need
- [ ] Adversarial verification - tested for broken links, missing context, unclear instructions

## See Also

- Related command: `/update-docs`
- Related command: `/generate-docs`
- Related command: `/docs-serve`
- Documentation templates: [Documentation Templates](../../docs/content/reference/docs/templates/index.md)
- Related rule: @docs/docs.mdc
- Related rule: @docs/style.mdc
- Related rule: @docs/syntax.mdc
- Related rule: @docs/structure.mdc
- Related rule: @docs/patterns.mdc
- Related rule: @docs/principals.mdc
- Related rule: @docs/zensical.mdc
