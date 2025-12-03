---
title: Documentation Best Practices
description: Documentation best practices for Tux development, including writing standards, structure guidelines, and quality assurance processes.
tags:
  - developer-guide
  - best-practices
  - documentation
---

# Documentation Best Practices

!!! warning "Work in progress"
    This section is a work in progress. Please help us by contributing to the documentation.

## Core Principles

### User-Centric Approach

**Focus on solving user problems, not describing code features.** Every documentation decision should answer: "How does this help someone using Tux?"

- **Users** need to understand how to use features
- **Admins** need to configure and manage servers  
- **Self-hosters** need deployment and maintenance guides
- **Developers** need API references and contribution guidelines

### Diátaxis Framework

Follow the [Diátaxis](https://diataxis.fr/) framework to organize documentation by user needs:

#### Four Documentation Types

- **Tutorials**: Learning-oriented guides that teach step-by-step
- **How-to Guides**: Goal-oriented instructions for specific tasks
- **Reference**: Information-oriented technical descriptions  
- **Explanation**: Understanding-oriented discussions of concepts

Choose the right type based on what users need to accomplish.

## Writing Standards

### Style Principles

- **Simple & Direct**: Use short sentences and active voice
- **Second Person**: Address users as "you" consistently
- **Present Tense**: Write in present simple consistently
- **Imperative Verbs**: Use action words (configure, install, run)

### Formatting Standards

- **Titles & Headings**: Use sentence case (not title case)
- **Inline Code**: `variables`, `file.md`, `config-options`
- **Code Blocks**: Always specify language (`bash`, `python`, `sql`, etc.)
- **Links**: Use descriptive text, not "click here"
- **Admonitions**: Use for warnings, notes, and tips

## Content Organization

### Directory Structure

```text
docs/content/
├── getting-started/    # Onboarding for different user types
├── user/               # Complete user experience
├── admin/              # Server administration
├── selfhost/           # Self-hosting guides
├── developer/          # Development resources
├── reference/          # Technical specifications
└── support/            # Support, changelog, FAQ
```

### File Naming & Navigation

- **Files**: Use `kebab-case.md` (e.g., `moderation-commands.md`)
- **Directories**: Use `kebab-case/` with `index.md` files
- **Navigation**: Use `SUMMARY.md` with wildcard patterns

## Quality Assurance

### Before Publishing

- [ ] **Purpose clear**: Introduction states what the page teaches/solves
- [ ] **Audience appropriate**: Content matches intended readers
- [ ] **Prerequisites listed**: Required knowledge/software upfront
- [ ] **Examples tested**: Code examples are functional
- [ ] **Links validated**: All references work
- [ ] **Builds cleanly**: `uv run zensical build --strict` passes

### Maintenance

- **Monthly**: Review high-traffic pages for outdated information
- **Quarterly**: Audit cross-references and navigation links  
- **Release**: Update documentation for new features

## Tooling & Workflow

### Development Workflow

```bash
# Local development
uv run docs serve

# Build for production
uv run docs build
```

### Quality Checks

- **Spellcheck**: Multi-backend validation
- **Link validation**: Automated cross-reference checking
- **Build validation**: Strict Zensical build requirements
- **Accessibility**: Semantic HTML and alt text validation

## Contributing to Documentation

### Getting Started

1. **Understand the codebase**: Study existing patterns
2. **Follow the rules**: Review this best practices guide
3. **Choose content type**: Use Diátaxis framework
4. **Write clearly**: Follow style and formatting standards

### Pull Request Process

1. **Test locally**: `uv run docs serve` to preview
2. **Build cleanly**: `uv run docs build --strict` passes
3. **Follow conventions**: Use conventional commit format
4. **Update navigation**: Modify SUMMARY.md if needed

## Resources

- [Diátaxis Framework](https://diataxis.fr/) - Documentation methodology
- [Write the Docs](https://www.writethedocs.org/) - Community and standards
- [Google Developer Style Guide](https://developers.google.com/style) - Technical writing
- [Zensical](https://zensical.org/) - Documentation platform
