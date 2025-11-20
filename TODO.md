# TODO.md

## Plugin System Stability

- [ ] **Document Plugin APIs** - Create a clear guide showing which parts of Tux plugins can safely use
- [ ] **Add Deprecation Warnings** - Set up warnings when old plugin code will be removed in future versions
- [ ] **Check Plugin Imports** - Review what plugins import and ensure they're using safe, stable code
- [ ] **Validate Plugins on Load** - Check plugins when they start up to catch problems early
- [ ] **Version Compatibility** - Document which Tux versions work with plugins and how to upgrade between versions
- [ ] **Plugin Error Handling** - Document how plugins should handle errors and exceptions
- [ ] **Plugin Examples** - Create simple step-by-step guides for building plugins
- [ ] **Test Plugin Compatibility** - Add tests to ensure plugins work correctly with the bot
- [ ] **Detect Breaking Changes** - Set up automatic checks to find code changes that might break plugins
- [ ] **Code Quality Checks** - Add rules to prevent plugins from using unsafe internal code

## Documentation & Types

- [ ] **Complete Documentation** - Make sure all features are properly explained in docs
- [ ] **Check Type Hints** - Verify all code has clear type information for better reliability
- [ ] **Documentation Inventory** - Ensure all important functions appear in documentation search

## Code Organization

- [ ] **Clean Up Internal Code** - Organize internal utilities and separate them from public APIs
- [ ] **Command-Line Tools** - Make CLI commands more reliable and programmable

Fix log channel ui not updating when channel is selected

FIx /config ranks create command not working

Setup sentry sdk for metrics

Set permission errors to not be sent to sentry
