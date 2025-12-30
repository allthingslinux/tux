# Create Discord Module

## Overview

Create a new Discord bot module (cog) following Tux project patterns and structure.

## Steps

1. **Plan Module Structure**
   - Determine module category (admin, config, features, fun, guild, info, levels, moderation, snippets, tools, utility)
   - Choose appropriate directory in `src/tux/modules/`
   - Plan command structure and functionality
   - Identify required permissions

2. **Create Module File**
   - Create new file in appropriate module directory
   - Inherit from `BaseCog` or specialized base (e.g., `ModerationCogBase`)
   - Add `__init__` method with bot parameter
   - Implement `setup` function for cog loading

3. **Implement Commands**
   - Use `@commands.hybrid_command` for hybrid commands
   - Add `@commands.guild_only()` if guild required
   - Add `@requires_command_permission()` for permissions
   - Implement command handlers with proper error handling
   - Use embeds from `tux.ui.embeds` for responses

4. **Register Module**
   - Add module to bot's cog loading system
   - Test module loads correctly
   - Verify commands are registered

## Checklist

- [ ] Module file created in appropriate directory
- [ ] Inherits from BaseCog or specialized base
- [ ] Commands use hybrid_command decorator
- [ ] Permission checks added with @requires_command_permission()
- [ ] Error handling implemented
- [ ] Uses embeds for responses
- [ ] Setup function implemented
- [ ] Module registered with bot
- [ ] Commands tested locally
- [ ] Commands synced to Discord

## See Also

- Related rule: @modules/cogs.mdc
- Related rule: @modules/commands.mdc
- Related command: `/discord-test-command`
