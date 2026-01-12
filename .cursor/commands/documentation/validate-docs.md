# Validate Documentation

## Overview

Perform a comprehensive audit of all documentation to identify incorrect, outdated, misleading, or wrong information. This command validates documentation accuracy against the actual codebase, configuration, and related systems with extreme detail.

## Steps

1. **Prepare Validation Environment**
   - Review documentation structure: `docs/content/`
   - Identify all documentation files to validate
   - Map documentation sections to their corresponding code/config
   - Gather all relevant codebase sources for cross-validation
   - Check documentation build status: `uv run docs build`
   - Note any existing build errors or warnings

2. **Audit Code Examples**

   **For each code example in documentation:**
   - Locate the actual implementation in codebase
   - Verify imports and dependencies exist and are correct
   - Test syntax and API usage against current codebase
   - Check that function/class/method signatures match documentation
   - Verify parameter names, types, and defaults are accurate
   - Confirm return types and exception handling match reality
   - Cross-reference with actual source code, not just docstrings
   - Check for deprecated APIs or patterns in examples
   - Verify examples use current best practices
   - Test if examples would actually execute (check for missing setup, context)
   - Compare with similar code examples in codebase for consistency
   - Verify error handling patterns match project standards
   - Check async/await usage is correct for current patterns
   - Validate type hints match actual implementation

3. **Validate CLI Commands**

   **For each CLI command documented:**
   - Find actual command implementation in `scripts/` directory
   - Verify command name, syntax, and options match documentation
   - Check all documented options actually exist in implementation
   - Verify option types, defaults, and descriptions are accurate
   - Test command help output against documentation
   - Confirm command paths (`uv run tux start`, not `python tux.py`)
   - Cross-reference with `pyproject.toml` script definitions
   - Verify command output examples match actual output
   - Check exit codes and error messages are documented correctly
   - Validate environment variable usage in commands
   - Verify command examples work when executed
   - Check for deprecated commands still documented
   - Confirm command grouping and organization matches structure

4. **Verify Configuration Documentation**

   **For each configuration option documented:**
   - Compare with actual config files: `config/*.example`, `config/*.toml.example`
   - Verify all documented options exist in actual config schemas
   - Check default values against actual code defaults (search codebase)
   - Validate configuration types match actual implementation
   - Cross-reference with Pydantic models or config classes
   - Verify environment variable mappings are correct
   - Check configuration examples work when applied
   - Validate validation rules and constraints match code
   - Confirm deprecated options are marked as deprecated
   - Check for undocumented configuration options
   - Verify Docker configuration matches `compose.yaml` or `Containerfile`
   - Cross-reference database config with actual database setup
   - Validate nested configuration structures match reality

5. **Audit Environment Variables**

   **For each environment variable documented:**
   - Search codebase for actual usage of each variable
   - Verify variable names match actual usage (case-sensitive)
   - Check default values against code (search for `os.getenv`, `os.environ`)
   - Validate variable documentation in all relevant files
   - Cross-reference with `.env.example` if it exists
   - Verify required vs optional status is accurate
   - Check for undocumented environment variables in use
   - Validate variable grouping and organization
   - Confirm variable descriptions match their actual purpose
   - Check for deprecated variables still documented

6. **Validate API References**

   **For each API endpoint, method, or service documented:**
   - Locate actual implementation in codebase
   - Verify method signatures match documentation exactly
   - Check parameter types, names, and requirements
   - Validate return types and response structures
   - Cross-reference with actual code, tests, and other docs
   - Verify authentication/authorization requirements
   - Check error responses and status codes are accurate
   - Validate request/response examples match implementation
   - Confirm API versioning if applicable
   - Check for deprecated endpoints still documented
   - Verify rate limiting and constraints match reality
   - Cross-reference with OpenAPI specs if available

7. **Validate Database Documentation**

   **For database-related documentation:**
   - Compare model documentation with actual SQLModel models
   - Verify field types, constraints, and relationships
   - Check migration documentation against Alembic migrations
   - Validate database service methods match documentation
   - Cross-reference query patterns with actual controller code
   - Verify database configuration matches actual setup
   - Check for schema changes not reflected in documentation
   - Validate relationship documentation (foreign keys, joins)
   - Confirm transaction patterns match implementation
   - Check index documentation matches actual indexes

8. **Audit Cross-References and Links**

   **For each internal link:**
   - Verify link target file exists at specified path
   - Check relative paths are correct (test navigation)
   - Confirm anchor links point to actual headings
   - Validate navigation structure in `zensical.toml`
   - Check for circular references or broken chains
   - Verify link text accurately describes target content
   - Cross-reference with actual file structure

   **For each external link:**
   - Test that URLs are accessible (if possible)
   - Verify URLs haven't changed or been deprecated
   - Check link text matches destination content
   - Validate external resources are still relevant
   - Note any broken or deprecated external links

9. **Validate Documentation Structure**

   - Verify Diátaxis framework is applied correctly:
     - Tutorials are learning-oriented with step-by-step guidance
     - How-to guides solve specific problems
     - Reference documentation provides comprehensive technical details
     - Explanations provide understanding-oriented content
   - Check documentation is in correct directory structure
   - Verify index pages exist and are complete
   - Validate heading hierarchy is consistent
   - Check navigation structure matches content organization
   - Verify cross-references use appropriate documentation type

10. **Audit Documentation Style and Formatting**

    - Verify active voice is used (not passive)
    - Check second person ("you") is used appropriately
    - Validate present simple tense usage
    - Check code blocks have language specifiers
    - Verify admonitions (tip, warning, note) are appropriate
    - Validate consistent list formatting
    - Check sentence case for titles and headings
    - Verify consistent terminology throughout
    - Check for placeholder text, TODOs, or incomplete sections
    - Validate formatting matches project standards (see @docs/style.mdc)

11. **Validate Content Accuracy**

    **For each factual claim:**
    - Cross-reference with actual codebase implementation
    - Verify against multiple sources (code, tests, config, other docs)
    - Check for outdated information by comparing with recent changes
    - Validate technical details against actual behavior
    - Confirm examples are realistic and match actual use cases
    - Check for contradictions between different documentation pages
    - Verify prerequisite information is accurate
    - Validate troubleshooting information matches actual issues
    - Check for misleading or incorrect guidance
    - Confirm version information is current

12. **Check for Missing Documentation**

    - Compare documented features with actual codebase features
    - Check for new features without documentation
    - Verify all public APIs are documented
    - Check for configuration options without documentation
    - Validate CLI commands are all documented
    - Check for database models without documentation
    - Verify important concepts are explained
    - Check for missing troubleshooting information
    - Validate all user-facing features are documented

13. **Audit Command/Feature Documentation**

    **For each Discord command documented:**
    - Find actual command implementation in `src/tux/modules/`
    - Verify command name, description, and usage match
    - Check permission requirements are accurate
    - Validate parameter documentation matches implementation
    - Cross-reference with command help text
    - Verify examples work in actual Discord context
    - Check for deprecated commands still documented
    - Confirm command grouping matches module structure

14. **Validate Build and Technical Issues**

    - Run documentation build: `uv run docs build`
    - Fix any build errors (syntax, references, formatting)
    - Check for build warnings that indicate issues
    - Verify all pages render correctly
    - Test documentation locally: `uv run docs serve`
    - Check for broken internal references
    - Validate Zensical syntax is correct
    - Verify navigation works correctly
    - Check search functionality works
    - Validate responsive design issues

15. **Context-Aware Validation**

    **For complex claims or features:**
    - Don't trust single source - cross-reference multiple locations
    - Search codebase for actual implementation patterns
    - Check tests for expected behavior
    - Review related configuration and setup files
    - Verify against similar features for consistency
    - Check commit history for recent changes
    - Validate against related documentation pages
    - Cross-reference with error handling and logging
    - Verify integration points match reality

16. **Create Validation Report**

    - List all issues found with severity levels:
      - **Critical**: Incorrect information, broken examples, wrong commands
      - **High**: Outdated information, missing documentation, broken links
      - **Medium**: Style issues, formatting problems, minor inaccuracies
      - **Low**: Suggestions for improvement, style consistency
    - Include file path and line number for each issue
    - Provide context: what's wrong, what should be, how to verify
    - Reference actual code/config for verification
    - Group issues by category (code examples, commands, config, etc.)
    - Prioritize critical and high-priority issues
    - Note any patterns of issues across documentation

## Validation Categories

### Code Accuracy

- Code examples match actual implementation
- Imports and dependencies are correct
- API usage matches current patterns
- Type hints are accurate
- Error handling patterns match code
- Async/await usage is correct

### Command Accuracy

- CLI commands match actual scripts
- Command syntax is correct
- Options and parameters are accurate
- Command paths are correct (`uv run`, not `python`)
- Help output matches documentation
- Examples execute successfully

### Configuration Accuracy

- Configuration options exist in actual config
- Default values match code defaults
- Types match implementation
- Environment variables are correct
- Validation rules match code
- Examples work when applied

### Link and Reference Accuracy

- Internal links target existing files
- Anchor links point to actual headings
- External links are accessible
- Navigation structure is correct
- Cross-references are accurate

### Content Accuracy

- Technical claims match implementation
- Examples are realistic and work
- Troubleshooting information is correct
- Prerequisites are accurate
- No contradictory information

### Structure and Organization

- Documentation follows Diátaxis framework
- Files are in correct directories
- Navigation structure matches content
- Index pages are complete
- Heading hierarchy is consistent

### Style and Formatting

- Follows project style guidelines
- Consistent terminology
- Proper code block formatting
- Appropriate admonitions
- No placeholder text

## Error Handling

**Critical Issues (Must Fix):**

- Code examples that don't work
- CLI commands with wrong syntax
- Configuration options that don't exist
- Broken internal links
- Incorrect API references
- Contradictory information

**High Priority Issues (Should Fix):**

- Outdated code examples
- Missing documentation for features
- Incorrect default values
- Broken external links
- Outdated API references
- Misleading guidance

**Medium Priority Issues (Consider Fixing):**

- Style inconsistencies
- Formatting issues
- Missing cross-references
- Minor inaccuracies
- Incomplete sections

**Low Priority Issues (Nice to Have):**

- Style suggestions
- Additional examples
- Improved organization
- Enhanced clarity

## Validation Checklist

- [ ] All code examples verified against actual codebase
- [ ] All CLI commands tested and verified
- [ ] All configuration options cross-referenced with actual config
- [ ] All environment variables verified against codebase usage
- [ ] All API references validated against implementation
- [ ] All database documentation matches models and migrations
- [ ] All internal links tested and verified
- [ ] All external links checked (if possible)
- [ ] Documentation structure validated (Diátaxis framework)
- [ ] Style and formatting checked against standards
- [ ] Content accuracy verified through multiple sources
- [ ] Missing documentation identified
- [ ] Command/feature documentation verified
- [ ] Documentation builds without errors
- [ ] Validation report created with all issues
- [ ] Critical and high-priority issues identified
- [ ] Context provided for each issue

## Examples

### Validating Code Example

1. Find code example in documentation
2. Search codebase for actual implementation
3. Verify imports match actual module structure
4. Check function signature matches documentation
5. Test if example would execute (check dependencies, context)
6. Compare with similar examples in codebase
7. Verify type hints match implementation
8. Check error handling patterns
9. Report any discrepancies with actual code

### Validating CLI Command

1. Find command documentation
2. Locate actual script in `scripts/` directory
3. Check command name and syntax match
4. Verify all options exist in implementation
5. Test command help output
6. Execute command example
7. Compare output with documentation
8. Check `pyproject.toml` for script definition
9. Report any inaccuracies or missing information

### Validating Configuration

1. Find configuration documentation
2. Compare with `config/*.example` files
3. Search codebase for actual default values
4. Check Pydantic models or config classes
5. Verify environment variable mappings
6. Test configuration example
7. Check validation rules in code
8. Cross-reference with Docker config
9. Report discrepancies or missing information

### Context-Aware Validation

1. Identify complex claim or feature
2. Search codebase in multiple locations:
   - Actual implementation
   - Tests for expected behavior
   - Configuration files
   - Related documentation
   - Error handling code
   - Logging statements
3. Cross-reference findings
4. Verify consistency across sources
5. Check for recent changes (git history)
6. Report any contradictions or inaccuracies

## See Also

- Related command: `/update-docs` - Update documentation for code changes
- Related command: `/deslop-docs` - Produce high-quality documentation
- Related command: `/generate-docs` - Generate API documentation
- Related command: `/docs-serve` - Start local documentation server
- Related rule: @docs/docs.mdc - Documentation standards master guide
- Related rule: @docs/style.mdc - Writing style and formatting
- Related rule: @docs/patterns.mdc - Documentation patterns and examples
- Related rule: @docs/principals.mdc - Diátaxis framework principles
- Related rule: @docs/syntax.mdc - Zensical syntax reference
- Related rule: @docs/structure.mdc - Documentation organization

## Additional Notes

- **Thoroughness**: This command emphasizes extreme detail and cross-referencing. Don't trust single sources - verify against multiple sources.
- **Context**: Always find context around documentation claims by checking code, tests, config, and related documentation.
- **Accuracy**: Focus on identifying incorrect, outdated, misleading, or wrong information.
- **Verification**: Provide evidence for issues found - reference actual code/config that contradicts documentation.
- **Prioritization**: Focus on critical and high-priority issues that affect user experience and accuracy.
- **Patterns**: Look for patterns of issues across documentation - this may indicate systemic problems.
