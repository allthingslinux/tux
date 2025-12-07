# Test Discord Command

## Overview

Test a Discord command locally to verify it works correctly before deploying.

## Steps

1. **Start Bot in Debug Mode**
   - Run `uv run tux start --debug`
   - Verify bot connects to Discord
   - Check for any startup errors
   - Verify command is loaded

2. **Test Command Execution**
   - Invoke command in Discord (slash or prefix)
   - Test with valid inputs
   - Test with invalid inputs
   - Test permission checks
   - Verify error handling works

3. **Check Logs**
   - Review loguru output for errors
   - Check Sentry for any exceptions
   - Verify command execution logs
   - Check for rate limit warnings

4. **Verify Responses**
   - Check embeds render correctly
   - Verify interaction responses work
   - Test ephemeral responses if applicable
   - Check button/select interactions

## Checklist

- [ ] Bot started in debug mode
- [ ] Command registered and visible
- [ ] Command executes with valid inputs
- [ ] Error handling works for invalid inputs
- [ ] Permission checks work correctly
- [ ] Responses render properly
- [ ] No errors in logs
- [ ] Interactions work correctly

## See Also

- Related rule: @modules/commands.mdc
- Related rule: @modules/interactions.mdc
- Related command: `/discord-create-module`
