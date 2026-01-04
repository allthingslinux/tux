# Update Documentation

## Overview

Comprehensively update documentation to reflect code changes, new features, configuration updates, or structural changes. This command ensures documentation stays current with the codebase and maintains high quality standards.

## Steps

1. **Identify Documentation Scope**
   - Review recent commits and changes: `git log --oneline -10`
   - Check current branch for new features or breaking changes
   - Identify affected documentation areas (user, admin, developer, API)
   - Note deprecated features requiring removal or migration guides
   - Check for new CLI commands or configuration options

2. **Audit Current Documentation**
   - Review existing documentation structure in `docs/content/`
   - Check for outdated information or broken examples
   - Identify missing documentation for new features
   - Verify cross-references and internal links
   - Check for inconsistent terminology or formatting

3. **Update Content by Category**

   **User Documentation (`docs/content/user/`)**
   - Update command references for new bot commands
   - Add usage examples for new features
   - Update FAQ with common questions
   - Verify all user-facing examples work

   **Admin Documentation (`docs/content/admin/`)**
   - Update configuration guides for new settings
   - Add setup instructions for new features
   - Update permission and role documentation
   - Verify deployment guides are current

   **Developer Documentation (`docs/content/developer/`)**
   - Update API documentation for code changes
   - Add guides for new development patterns
   - Update architecture documentation
   - Verify setup and contribution guides

   **Reference Documentation (`docs/content/reference/`)**
   - Update CLI command references
   - Add new configuration options
   - Update API reference documentation
   - Verify all code examples and snippets

4. **Follow Documentation Standards**
   - Apply Diátaxis framework principles:
     - **Tutorials**: Learning-oriented, hands-on lessons
     - **How-to guides**: Problem-oriented, practical steps
     - **Reference**: Information-oriented, comprehensive details
     - **Explanation**: Understanding-oriented, theoretical knowledge
   - Follow Zensical syntax and conventions (see @docs/zensical.mdc)
   - Use consistent writing style (see @docs/style.mdc)
   - Include practical, working examples
   - Add appropriate admonitions (tip, warning, note, etc.)

5. **Verify Code Examples**
   - Test all code snippets and commands
   - Verify CLI commands work with current syntax
   - Check configuration examples against actual config files
   - Update import statements and API usage
   - Ensure examples use current best practices

6. **Update Cross-References**
   - Check internal links between documentation pages
   - Update references to moved or renamed files
   - Verify external links are still valid
   - Add new cross-references for related content
   - Update navigation structure if needed

7. **Check Configuration Documentation**
   - Compare with actual config files in `config/`
   - Verify environment variable documentation
   - Update Docker and deployment configuration
   - Check database configuration examples
   - Verify all configuration options are documented

8. **Update CLI Documentation**
   - Check CLI commands in `scripts/` directory
   - Verify command syntax and options
   - Update help text and examples
   - Add documentation for new scripts
   - Remove documentation for deprecated commands

9. **Review Media and Assets**
   - Update screenshots if UI changed
   - Verify image links and alt text
   - Check for outdated diagrams or flowcharts
   - Update banner or promotional images if needed
   - Optimize images for web performance

10. **Build and Test Documentation**
    - Run `uv run docs build` to build the site
    - Fix any build errors or warnings
    - Check for broken links or missing references
    - Verify all pages render correctly
    - Test responsive design on different screen sizes

11. **Local Preview and Review**
    - Start local server: `uv run docs serve`
    - Navigate through all updated sections
    - Test search functionality with new content
    - Verify navigation and table of contents
    - Check formatting, syntax highlighting, and admonitions

12. **Validate Documentation Quality**
    - Ensure all new features are documented
    - Verify examples are practical and helpful
    - Check that documentation follows project voice/tone
    - Ensure accessibility guidelines are followed
    - Verify SEO considerations (titles, descriptions, headings)

## Special Considerations

### Breaking Changes

- Create migration guides for breaking changes
- Add deprecation warnings with timelines
- Provide before/after examples
- Update version compatibility information

### New Features

- Add comprehensive usage examples
- Include common use cases and patterns
- Provide troubleshooting information
- Add to appropriate getting started guides

### API Changes

- Update all affected API documentation
- Add changelog entries for API changes
- Update SDK or client library examples
- Verify backward compatibility notes

### Configuration Changes

- Update all configuration examples
- Add validation information for new settings
- Document default values and ranges
- Provide migration instructions if needed

## Error Handling

**Build Errors:**

- Check Zensical syntax and formatting
- Verify all referenced files exist
- Fix broken internal links
- Resolve missing images or assets

**Content Issues:**

- Verify all code examples work
- Check for outdated information
- Fix inconsistent terminology
- Resolve conflicting instructions

**Navigation Issues:**

- Update table of contents structure
- Fix broken cross-references
- Verify sidebar navigation
- Check breadcrumb navigation

## Update Checklist

- [ ] Documentation scope identified and planned
- [ ] Current documentation audited for issues
- [ ] User documentation updated for new features
- [ ] Admin documentation updated for configuration changes
- [ ] Developer documentation updated for API changes
- [ ] Reference documentation updated and comprehensive
- [ ] Diátaxis framework principles applied
- [ ] Zensical syntax and style guidelines followed
- [ ] All code examples tested and verified
- [ ] Cross-references and links updated
- [ ] Configuration documentation matches actual config
- [ ] CLI documentation matches current commands
- [ ] Media and assets updated as needed
- [ ] Documentation builds without errors
- [ ] Local preview reviewed thoroughly
- [ ] Search functionality tested with new content
- [ ] Navigation and UX verified
- [ ] Quality standards met (accessibility, SEO, etc.)

## Examples

### Updating for New Bot Command

1. Add command to user guide with usage examples
2. Update admin guide if command requires permissions
3. Add to CLI reference documentation
4. Update FAQ if command addresses common questions
5. Add cross-references from related documentation
6. Test all examples in actual Discord server

### Updating for Configuration Change

1. Update configuration reference documentation
2. Add examples to admin setup guide
3. Update Docker and deployment documentation
4. Add migration guide if breaking change
5. Update troubleshooting documentation
6. Verify all configuration examples work

### Updating for API Change

1. Update API reference documentation
2. Update developer guides and tutorials
3. Add changelog entry with migration notes
4. Update code examples throughout documentation
5. Add deprecation warnings if applicable
6. Test all API examples against current codebase

## See Also

- Related rule: @docs/docs.mdc - Documentation standards and patterns
- Related rule: @docs/zensical.mdc - Zensical syntax and features
- Related rule: @docs/style.mdc - Writing style guidelines
- Related command: `/generate-docs` - Generate API documentation
- Related command: `/docs-serve` - Start local documentation server

## Additional Notes

- **Frequency**: Update documentation with every feature release or significant change
- **Quality**: Prioritize clarity, accuracy, and practical examples
- **Maintenance**: Regularly audit documentation for outdated information
- **User Focus**: Write from the user's perspective and use cases
- **Testing**: Always test examples and instructions before publishing
- **Feedback**: Monitor user questions to identify documentation gaps
