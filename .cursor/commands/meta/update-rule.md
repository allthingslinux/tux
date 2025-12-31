# Update Cursor Rule

## Overview

Audit and update an existing Cursor rule to ensure it's current with project standards, dependencies, and codebase patterns. This command guides you through validation, verification, and updates.

## Steps

1. **Identify Rule to Update**
   - Locate the rule file in `.cursor/rules/{domain}/{rule-name}.mdc`
   - Open the rule file for review
   - Note the domain and rule type (always-apply, intelligent, file-scoped, manual)

2. **Run Validation**
   - Execute: `uv run ai validate-rules`
   - Fix any validation errors found:
     - Frontmatter format issues
     - Description length (60-120 chars for intelligent rules)
     - Globs format (comma-separated, no quotes/brackets)
     - Missing content (title, patterns, examples)
     - File size (max 500 lines, except for exceptions)

3. **Verify Dependencies (for tech-stack rules)**
   - Check `pyproject.toml` for current dependencies
   - Compare with dependencies listed in rule
   - Verify versions match actual package versions
   - Check for new dependencies not in rule
   - Check for removed dependencies still in rule
   - Update dependency lists as needed

4. **Verify Code Examples**
   - Check if code examples still work
   - Verify file paths/structures still exist
   - Test code snippets against current codebase
   - Update examples if patterns have changed
   - Ensure examples use current API patterns

5. **Verify Cross-References**
   - Check `@domain/rule-name.mdc` references point to existing rules
   - Verify `/command-name` references point to existing commands
   - Check `@AGENTS.md` and other file references
   - Update or remove broken references

6. **Check Project Patterns**
   - Review actual codebase patterns the rule describes
   - Verify rule matches current project practices
   - Check if patterns have evolved since rule was written
   - Update patterns section if needed
   - Add new ✅ GOOD examples for current patterns
   - Add new ❌ BAD examples for anti-patterns found

7. **Review CLI Commands**
   - For rules mentioning CLI commands, verify commands still exist
   - Check command syntax in `scripts/` directory
   - Update command examples if syntax changed
   - Verify script paths and names are correct

8. **Check Configuration**
   - If rule mentions configuration files, verify they exist
   - Check config file formats match current structure
   - Verify environment variables are current
   - Update config examples if format changed

9. **Verify File Structure**
   - If rule mentions project structure, verify directories exist
   - Check file organization matches rule description
   - Update structure documentation if changed
   - Verify glob patterns match actual file locations

10. **Review Best Practices**
    - Ensure best practices are still valid
    - Add new practices if patterns evolved
    - Remove obsolete practices
    - Update practices to match current standards

11. **Review Anti-Patterns**
    - Verify anti-patterns are still relevant
    - Add new anti-patterns if discovered
    - Remove anti-patterns that are no longer applicable
    - Update examples to match current codebase

12. **Check Related Documentation**
    - Review `AGENTS.md` for consistency
    - Check related rules in same domain
    - Ensure no contradictions with other rules
    - Update See Also section if needed

13. **Validate Again**
    - Run `uv run ai validate-rules` after updates
    - Fix any new validation errors
    - Ensure rule still passes all checks

14. **Test Rule**
    - @-mention the rule in Cursor chat
    - Verify rule applies correctly
    - Check that examples are helpful
    - Ensure rule provides value in context

## Special Checks by Rule Type

### Tech Stack Rules (`core/tech-stack.mdc`)

- Compare dependencies with `pyproject.toml`
- Verify Python version requirements
- Check build system matches
- Verify tool versions and configurations
- Check Docker setup matches `compose.yaml`
- Verify database versions and drivers

### Database Rules

- Check SQLModel version and features
- Verify migration patterns with Alembic
- Check controller patterns match implementation
- Verify query patterns are current
- Check database service patterns

### Module Rules

- Verify Discord.py version and API
- Check command patterns match current usage
- Verify event handler patterns
- Check interaction patterns (Components V2)
- Verify permission patterns

### Testing Rules

- Check pytest configuration matches `pyproject.toml`
- Verify test markers are current
- Check fixture patterns match implementation
- Verify coverage configuration
- Check async testing patterns

### Documentation Rules

- Verify Zensical setup and config
- Check documentation structure
- Verify markdown syntax and extensions
- Check deployment workflow

## Error Handling

If validation fails:

- **Frontmatter errors**: Fix YAML format, ensure `---` delimiters
- **Description errors**: Adjust to 60-120 chars, add domain keywords
- **Globs errors**: Use comma-separated format, no quotes/brackets
- **Content errors**: Add missing sections (title, patterns, examples)
- **Size errors**: Split rule if over 500 lines

If examples don't match codebase:

- Update code examples to current patterns
- Remove obsolete examples
- Add new examples for current practices
- Verify examples work in context

If dependencies are outdated:

- Compare with `pyproject.toml` dependencies
- Update version numbers
- Add missing dependencies
- Remove deprecated dependencies
- Group dependencies correctly

If cross-references are broken:

- Find correct rule/command paths
- Update references to correct names
- Remove references to deleted items
- Add references to new related items

## Update Checklist

- [ ] Rule file identified and opened
- [ ] Validation run (`uv run ai validate-rules`)
- [ ] All validation errors fixed
- [ ] Dependencies checked against `pyproject.toml` (if applicable)
- [ ] Code examples verified against codebase
- [ ] Cross-references checked and updated
- [ ] Project patterns reviewed and updated
- [ ] CLI commands verified (if mentioned)
- [ ] Configuration checked (if mentioned)
- [ ] File structure verified (if mentioned)
- [ ] Best practices reviewed and updated
- [ ] Anti-patterns reviewed and updated
- [ ] Related documentation checked for consistency
- [ ] Rule validated again after updates
- [ ] Rule tested via @-mention in chat

## Examples

### Updating tech-stack.mdc

1. Run: `uv run ai validate-rules` (fix any errors)
2. Open `pyproject.toml` and compare dependencies
3. Check Python version: `>=3.13.2,<3.14`
4. Verify build system: `hatchling`
5. Compare dependency groups with rule
6. Check line length in ruff config (88 chars)
7. Verify database driver: `psycopg[binary,pool]`
8. Check Docker services match `compose.yaml`
9. Update any outdated information
10. Validate again and test

### Updating a Database Rule

1. Validate rule structure
2. Check SQLModel imports in codebase
3. Verify controller patterns match implementation
4. Check migration patterns with Alembic
5. Review query examples for accuracy
6. Update patterns if codebase evolved
7. Verify cross-references to related rules
8. Test rule in context

### Updating a Module Rule

1. Validate rule structure
2. Check Discord.py version and features
3. Verify command decorators match usage
4. Check event handler patterns
5. Review interaction patterns (Components V2)
6. Update examples to current API
7. Verify permission check patterns
8. Test rule with actual modules

## See Also

- Related command: `/create-rule` - Create a new rule
- Related command: `/validate-rules` - Validate all rules
- Related rule: @meta/cursor-rules.mdc - Rules specification
- Related rule: @core/tech-stack.mdc - Tech stack reference
- Related rule: @.cursor/rules/rules.mdc - Rules catalog
- Related guide: [Creating Cursor Rules Guide](../../../docs/content/developer/guides/creating-cursor-rules.md)

## Additional Notes

- **Frequency**: Update rules when project patterns change, dependencies update, or examples become outdated
- **Validation**: Always validate after making changes
- **Testing**: Test rules in context to ensure they're helpful
- **Consistency**: Ensure rules don't contradict each other
- **Examples**: Keep examples current and working
- **Cross-references**: Keep See Also section up to date
- **Documentation**: Update related docs if rule changes significantly
