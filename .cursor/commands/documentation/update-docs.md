# Update Documentation

## Overview

Update documentation to reflect code changes, new features, or configuration updates.

## Steps

1. **Identify Changes**
   - Review code changes in current branch
   - Note new features or commands
   - Check for configuration changes
   - Identify deprecated features

2. **Update Relevant Sections**
   - Update user guides for new features
   - Update admin documentation for new commands
   - Update developer docs for API changes
   - Update configuration documentation

3. **Follow Documentation Standards**
   - Use Diátaxis framework (tutorial, how-to, reference, explanation)
   - Follow writing style guidelines
   - Use appropriate Zensical syntax (see @docs/style.mdc)
   - Include practical examples

4. **Test Documentation**
   - Build documentation: `uv run docs build`
   - Serve locally: `uv run docs serve`
   - Review rendered pages
   - Test all links and examples

## Checklist

- [ ] Code changes identified
- [ ] Relevant documentation sections updated
- [ ] Documentation standards followed
- [ ] Examples included
- [ ] Documentation built successfully
- [ ] Local preview reviewed
- [ ] Links tested
- [ ] Examples verified

## See Also

- Related rule: @docs/docs.mdc
- Related rule: @docs/style.mdc
- Related command: `/generate-docs`
- Related command: `/docs-serve`
