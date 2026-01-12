# Serve Documentation

## Overview

Start and manage a local documentation server to preview documentation changes, test new content, and validate the complete documentation experience before deployment. This command provides comprehensive testing and validation of documentation builds.

## Steps

1. **Prepare Documentation Environment**
   - Ensure documentation is built: `uv run docs build`
   - Check for any build errors or warnings
   - Verify all dependencies are installed
   - Clear any cached documentation if needed
   - Check available ports (default: 8000)

2. **Start Documentation Server**
   - Run `uv run docs serve` to start the local server
   - Note the server URL (typically `http://localhost:8000`)
   - Verify server starts without errors
   - Check console output for any warnings
   - Confirm auto-reload functionality is active

3. **Validate Server Configuration**
   - Verify server is accessible in browser
   - Check that all static assets load correctly
   - Confirm CSS and JavaScript are working
   - Test that images and media files display
   - Verify favicon and site metadata

4. **Test Documentation Navigation**
   - Navigate through all main sections
   - Test sidebar navigation and collapsible sections
   - Verify breadcrumb navigation works
   - Check table of contents functionality
   - Test mobile navigation and responsive design

5. **Validate Content Rendering**
   - Check all pages render correctly
   - Verify code syntax highlighting works
   - Test admonitions (tip, warning, note, etc.)
   - Confirm tables and lists format properly
   - Check that math equations render (if applicable)

6. **Test Interactive Features**
   - Test search functionality with various queries
   - Verify search results are relevant and complete
   - Check search highlighting and navigation
   - Test any interactive code examples
   - Verify copy-to-clipboard functionality

7. **Validate Links and References**
   - Test all internal links between pages
   - Verify external links open correctly
   - Check anchor links within pages
   - Test cross-references and see-also sections
   - Verify API reference links work

8. **Test Code Examples**
   - Verify all code blocks display correctly
   - Check syntax highlighting for different languages
   - Test copy functionality for code snippets
   - Verify line numbers and highlighting
   - Check that long code blocks scroll properly

9. **Validate Responsive Design**
   - Test on different screen sizes
   - Verify mobile navigation works
   - Check tablet and desktop layouts
   - Test touch interactions on mobile
   - Verify text remains readable at all sizes

10. **Performance and Accessibility Testing**
    - Check page load times
    - Verify images are optimized
    - Test with screen readers (if available)
    - Check keyboard navigation
    - Verify color contrast and accessibility

11. **Test Auto-Reload Functionality**
    - Make a small change to a documentation file
    - Verify the browser automatically refreshes
    - Check that changes appear immediately
    - Test with different file types (markdown, config, assets)
    - Confirm no manual refresh is needed

12. **Monitor Server Logs**
    - Watch console output for errors or warnings
    - Check for 404 errors or missing resources
    - Monitor performance metrics if available
    - Note any deprecation warnings
    - Check for security warnings

13. **Test Documentation Features**
    - Verify version selector works (if applicable)
    - Test language switching (if multilingual)
    - Check dark/light mode toggle
    - Test print functionality
    - Verify social sharing features

14. **Validate SEO and Metadata**
    - Check page titles and descriptions
    - Verify Open Graph tags
    - Check structured data markup
    - Test social media preview cards
    - Verify canonical URLs

15. **Stop Server Safely**
    - Use Ctrl+C to stop the server gracefully
    - Verify all processes terminate properly
    - Check that ports are released
    - Note any cleanup warnings or errors

## Server Configuration

### Default Settings

- **Port**: 8000 (configurable)
- **Host**: localhost (127.0.0.1)
- **Auto-reload**: Enabled
- **Live-reload**: Browser refresh on file changes
- **Watch**: All documentation source files

### Custom Configuration

- **Dev Address**: Use `--dev-addr` (or `-a`) flag to specify IP address and port (format: `host:port`, default: `localhost:8000`)
- **Open Browser**: Use `--open` (or `-o`) flag to automatically open browser on start
- **Strict Mode**: Use `--strict` (or `-s`) flag for strict mode (not yet supported by zensical)

## Testing Scenarios

### New Content Testing

1. Add new documentation page
2. Verify it appears in navigation
3. Test all links to and from the page
4. Check formatting and styling
5. Verify search includes new content

### Content Updates Testing

1. Modify existing documentation
2. Verify changes appear immediately
3. Check that formatting is preserved
4. Test updated examples and code
5. Verify cross-references still work

### Asset Testing

1. Add new images or media files
2. Verify they display correctly
3. Check different image formats
4. Test responsive image behavior
5. Verify alt text and accessibility

### Configuration Testing

1. Modify site configuration
2. Restart server to apply changes
3. Verify configuration takes effect
4. Test navigation and structure changes
5. Check theme and styling updates

## Troubleshooting

### Server Won't Start

- Check if port is already in use
- Verify documentation builds successfully
- Check for missing dependencies
- Try different port with `--dev-addr` flag (e.g., `--dev-addr localhost:3000`)
- Check file permissions

### Pages Don't Load

- Verify build completed successfully
- Check for broken internal links
- Verify file paths are correct
- Check for case sensitivity issues
- Clear browser cache

### Auto-Reload Not Working

- Check file system permissions
- Verify watch functionality is enabled
- Try restarting the server
- Check for file system limitations
- Use manual refresh as fallback

### Styling Issues

- Clear browser cache and reload
- Check for CSS build errors
- Verify static assets are loading
- Check browser developer tools
- Try different browser

### Search Not Working

- Verify search index is built
- Check for JavaScript errors
- Clear browser cache
- Verify search configuration
- Test with simple queries first

## Validation Checklist

- [ ] Documentation environment prepared
- [ ] Server started successfully on correct port
- [ ] Server configuration validated
- [ ] Navigation tested thoroughly
- [ ] Content rendering verified
- [ ] Interactive features tested
- [ ] All links and references validated
- [ ] Code examples display correctly
- [ ] Responsive design tested
- [ ] Performance and accessibility checked
- [ ] Auto-reload functionality verified
- [ ] Server logs monitored for issues
- [ ] Documentation features tested
- [ ] SEO and metadata validated
- [ ] Server stopped safely

## Examples

### Basic Server Start

```bash
uv run docs serve
# Server starts on http://localhost:8000
# Auto-reload enabled
# Watch all documentation files
```

### Custom Port and Host

```bash
uv run docs serve --dev-addr 0.0.0.0:3000
# Server accessible on all network interfaces
# Custom port for avoiding conflicts
```

### Development Mode with Auto-Open

```bash
uv run docs serve --open
# Automatically opens browser on start
# Live reload enabled by default
# Immediate reflection of changes
```

### Testing Workflow

1. Start server: `uv run docs serve`
2. Open browser to `http://localhost:8000`
3. Navigate through documentation
4. Make test changes to files
5. Verify auto-reload works
6. Test all interactive features
7. Stop server with Ctrl+C

## See Also

- Related rule: @docs/zensical.mdc - Zensical configuration and features
- Related rule: @docs/docs.mdc - Documentation standards and patterns
- Related command: `/update-docs` - Update existing documentation
- Related command: `/generate-docs` - Generate new documentation

## Additional Notes

- **Development**: Use serve command during active documentation development
- **Testing**: Always test documentation locally before committing changes
- **Performance**: Monitor server performance with large documentation sites
- **Collaboration**: Share local server URL for team review (use `--dev-addr 0.0.0.0:8000`)
- **Automation**: Consider integrating serve command into development workflows
- **Debugging**: Use browser developer tools and server console output for troubleshooting
