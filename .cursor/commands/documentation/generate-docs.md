# Generate Documentation

## Overview

Generate comprehensive API documentation, update reference materials, and create documentation for new code changes. This command ensures all code is properly documented with examples, references, and integration guides.

## Steps

1. **Analyze Codebase Changes**
   - Review recent commits for new functions, classes, or modules
   - Identify new API endpoints or service methods
   - Check for new CLI commands or scripts
   - Note configuration changes or new settings
   - Identify breaking changes requiring migration documentation

2. **Audit Existing Documentation Coverage**
   - Check `docs/content/reference/` for missing API documentation
   - Review developer guides for outdated code examples
   - Identify undocumented public APIs or methods
   - Check for missing docstrings in new code
   - Verify existing documentation matches current implementation

3. **Generate API Reference Documentation**
   - Document new public classes and methods
   - Add comprehensive docstrings following NumPy format
   - Include parameter types, return values, and exceptions
   - Add usage examples for complex APIs
   - Document class hierarchies and relationships

4. **Update Code Examples**
   - Create practical examples for new features
   - Update existing examples to use current APIs
   - Add integration examples showing real-world usage
   - Include error handling in examples
   - Verify all examples work with current codebase

5. **Document New CLI Commands**
   - Add command reference documentation
   - Include all options and parameters
   - Provide usage examples and common patterns
   - Document command output and exit codes
   - Add troubleshooting information

6. **Update Configuration Documentation**
   - Document new configuration options
   - Include default values and valid ranges
   - Provide configuration examples
   - Add validation rules and constraints
   - Document environment variable mappings

7. **Create Integration Guides**
   - Write guides for new service integrations
   - Document API authentication and setup
   - Include step-by-step integration examples
   - Add troubleshooting and common issues
   - Provide testing and validation steps

8. **Generate Database Documentation**
   - Document new database models and relationships
   - Add migration guides for schema changes
   - Include query examples and patterns
   - Document database service methods
   - Add performance considerations

9. **Update Developer Guides**
   - Add guides for new development patterns
   - Update architecture documentation
   - Include new testing patterns or fixtures
   - Document new build or deployment processes
   - Add debugging and troubleshooting guides

10. **Create Tutorial Content**
    - Write step-by-step tutorials for new features
    - Include complete working examples
    - Add prerequisite information and setup
    - Provide expected outcomes and validation
    - Include next steps and advanced usage

11. **Generate Reference Materials**
    - Create comprehensive API reference pages
    - Add command-line reference documentation
    - Include configuration reference with all options
    - Document error codes and messages
    - Add glossary terms for new concepts

12. **Build and Validate Documentation**
    - Run `uv run docs build` to generate site
    - Fix any build errors or warnings
    - Validate all generated links work
    - Check code syntax highlighting
    - Verify all examples render correctly

13. **Test Generated Documentation**
    - Start local server: `uv run docs serve`
    - Navigate through all new documentation
    - Test all code examples and commands
    - Verify cross-references and navigation
    - Check responsive design and accessibility

## Documentation Types

### API Documentation

- **Classes**: Full class documentation with methods and properties
- **Functions**: Parameter types, return values, exceptions, examples
- **Services**: Service methods, dependencies, configuration
- **Models**: Database models, relationships, validation rules

### CLI Documentation

- **Commands**: Syntax, options, examples, output format
- **Scripts**: Purpose, usage, configuration, troubleshooting
- **Tools**: Installation, setup, common workflows

### Configuration Documentation

- **Settings**: All configuration options with types and defaults
- **Environment**: Environment variables and their mappings
- **Files**: Configuration file formats and examples
- **Validation**: Rules, constraints, and error messages

### Integration Documentation

- **APIs**: Authentication, endpoints, request/response formats
- **Services**: Setup, configuration, usage patterns
- **Databases**: Connection, queries, migrations, performance
- **External**: Third-party integrations and dependencies

## Quality Standards

### Code Examples

- **Working**: All examples must execute successfully
- **Complete**: Include necessary imports and setup
- **Realistic**: Use practical, real-world scenarios
- **Current**: Use latest API patterns and best practices
- **Tested**: Verify examples work with current codebase

### Documentation Structure

- **Organized**: Logical hierarchy and navigation
- **Searchable**: Proper headings and keywords
- **Linked**: Cross-references and related content
- **Accessible**: Screen reader friendly, proper alt text
- **Mobile**: Responsive design for all devices

### Content Quality

- **Clear**: Simple, direct language
- **Accurate**: Matches current implementation
- **Complete**: Covers all necessary information
- **Helpful**: Practical guidance and troubleshooting
- **Maintained**: Regular updates and validation

## Error Handling

**Missing Documentation:**

- Identify undocumented public APIs
- Add comprehensive docstrings
- Create reference documentation
- Add usage examples

**Outdated Examples:**

- Update code examples to current APIs
- Fix deprecated method usage
- Update import statements
- Verify examples work

**Build Failures:**

- Fix syntax errors in documentation
- Resolve missing references
- Update broken links
- Fix formatting issues

**Incomplete Coverage:**

- Add missing API documentation
- Document all public methods
- Include configuration options
- Add troubleshooting guides

## Generation Checklist

- [ ] Codebase changes analyzed and documented
- [ ] Existing documentation coverage audited
- [ ] New API reference documentation created
- [ ] Code examples updated and tested
- [ ] CLI commands documented with examples
- [ ] Configuration documentation updated
- [ ] Integration guides created for new features
- [ ] Database documentation updated
- [ ] Developer guides updated with new patterns
- [ ] Tutorial content created for complex features
- [ ] Reference materials comprehensive and current
- [ ] Documentation builds without errors
- [ ] All generated content tested and validated
- [ ] Cross-references and navigation verified
- [ ] Quality standards met (clarity, accuracy, completeness)

## Examples

### Generating API Documentation for New Service

1. Review service class and public methods
2. Add comprehensive docstrings with examples
3. Create API reference page in `docs/content/reference/`
4. Add integration guide in developer documentation
5. Include configuration examples
6. Add troubleshooting section
7. Test all examples and build documentation

### Documenting New CLI Command

1. Analyze command implementation and options
2. Create command reference documentation
3. Add usage examples for common scenarios
4. Include output format documentation
5. Add troubleshooting and error handling
6. Update CLI reference index
7. Test command examples and verify accuracy

### Creating Tutorial for New Feature

1. Identify target audience and prerequisites
2. Create step-by-step tutorial with working examples
3. Include setup and configuration steps
4. Add validation and testing instructions
5. Provide troubleshooting and next steps
6. Test complete tutorial from start to finish
7. Add to appropriate tutorial section

## See Also

- Related rule: @docs/docs.mdc - Documentation standards and patterns
- Related rule: @docs/zensical.mdc - Zensical syntax and features
- Related rule: @docs/style.mdc - Writing style guidelines
- Related command: `/update-docs` - Update existing documentation
- Related command: `/validate-docs` - Audit documentation for validity and accuracy
- Related command: `/docs-serve` - Start local documentation server

## Additional Notes

- **Automation**: Consider automating API documentation generation where possible
- **Consistency**: Maintain consistent format and style across all documentation
- **Examples**: Prioritize practical, working examples over theoretical descriptions
- **Maintenance**: Set up processes to keep generated documentation current
- **Feedback**: Monitor user questions to identify documentation gaps
- **Integration**: Ensure generated docs integrate well with existing content
