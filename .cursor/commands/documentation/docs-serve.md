# Serve Documentation

## Overview

Start local documentation server to preview documentation changes.

## Steps

1. **Start Documentation Server**
   - Run `uv run docs serve`
   - Server starts on default port (usually 8000)
   - Open browser to view documentation
   - Note the local URL

2. **Preview Changes**
   - Navigate to updated pages
   - Check formatting and styling
   - Test interactive features
   - Verify code examples render

3. **Test Navigation**
   - Check all navigation links work
   - Test search functionality
   - Verify cross-references
   - Check mobile responsiveness

4. **Stop Server**
   - Press Ctrl+C to stop server
   - Or close terminal window
   - Server stops automatically

## Notes

- Server auto-reloads on file changes
- Default port is usually 8000
- Access at `http://localhost:8000`
- Changes are visible immediately

## Checklist

- [ ] Documentation server started
- [ ] Documentation accessible in browser
- [ ] Changes previewed
- [ ] Formatting verified
- [ ] Navigation tested
- [ ] Links work correctly
- [ ] Examples render properly

## See Also

- Related rule: @docs/zensical.mdc
- Related command: `/generate-docs`
- Related command: `/update-docs`
