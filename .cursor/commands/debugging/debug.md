# Debug Issue

## Overview

Debug Discord bot issues systematically using Tux project tools and Discord.py debugging capabilities.

## Steps

1. **Problem Analysis**
   - Check loguru output in `logs/` directory
   - Review Sentry error traces
   - Examine Discord API error codes
   - Verify database state with `uv run db health`
2. **Discord Bot Debugging**
   - Enable debug mode: `uv run tux start --debug`
   - Check Discord gateway events and intents
   - Verify command registration and sync
   - Test interaction responses and timeouts
3. **Python Debugging Tools**
   - Add breakpoints with `breakpoint()`
   - Use loguru with `.debug()` level
   - Run pytest with `-vv -s` for verbose output
   - Check type errors with `uv run basedpyright`
4. **Database Debugging**
   - Check migrations with `uv run db status`
   - Verify queries with database logging
   - Test with pytest database fixtures
   - Use `uv run db reset` for clean state

## Debug Checklist

- [ ] Reviewed loguru logs in `logs/` directory
- [ ] Checked Sentry error dashboard
- [ ] Ran bot in debug mode
- [ ] Verified Discord gateway connection
- [ ] Checked command registration status
- [ ] Added debug logging at critical points
- [ ] Ran type checks with basedpyright
- [ ] Verified database migrations applied
- [ ] Ran relevant pytest tests with `-vv -s`
- [ ] Tested fix in isolated environment
