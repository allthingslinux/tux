# Tux Bot Testing TODO

Manual testing checklist for all modules and commands in the Tux Discord bot.

## Admin Commands

### dev.py - Development Commands

- [ ] `dev` (group command)
  - [ ] `dev sync_tree` - Sync command tree
  - [x] `dev clear_tree` - Clear command tree
  - [x] `dev load_cog` - Load a cog
  - [x] `dev unload_cog` - Unload a cog
  - [x] `dev reload_cog` - Reload a cog
  - [ ] `dev stop` - Stop the bot

### eval.py - Code Evaluation

- [ ] `eval` - Evaluate Python code

### git.py - Git Integration

- [ ] `git` (group command)
  - [ ] `git get_repo` - Get repository information
  - [ ] `git create_issue` - Create GitHub issue
  - [ ] `git get_issue` - Get GitHub issue

### mail.py - Mail System

- [ ] `mail register` - Register for mail system

### mock.py - Mock/Testing Commands

- [ ] `mock` (group command)
  - [ ] `mock error` - Mock error command
  - [ ] `mock test` - Mock test command

### permissions.py - Permission Management

- [ ] `permission` (group command)
  - [ ] `permission setup` - Setup permissions
  - [ ] `permission assign` - Assign permission level to role
  - [ ] `permission unassign` - Remove permission assignment
  - [ ] `permission assignments` - List permission assignments
  - [ ] `permission export` - Export permission configuration
  - [ ] `permission level` (subgroup)
    - [ ] `permission level create` - Create permission level
    - [ ] `permission level list` - List permission levels
    - [ ] `permission level delete` - Delete permission level
  - [ ] `permission command` (subgroup)
    - [ ] `permission command set` - Set command permission
    - [ ] `permission command list` - List command permissions
  - [ ] `permission blacklist` (subgroup)
    - [ ] `permission blacklist user` - Blacklist user/role/channel
    - [ ] `permission blacklist remove` - Remove from blacklist

## Fun Commands

### fact.py - Random Facts

- [ ] `fact` - Get random fact

### imgeffect.py - Image Effects

- [ ] `imgeffect deepfry` - Apply deepfry effect to image

### rand.py - Random Commands

- [ ] `random` (group command)
  - [ ] `random coinflip` - Flip a coin
  - [ ] `random 8ball` - Magic 8-ball
  - [ ] `random dice` - Roll dice
  - [ ] `random number` - Generate random number

### xkcd.py - XKCD Comics

- [x] `xkcd` (group command)
  - [x] `xkcd latest` - Get latest XKCD comic
  - [x] `xkcd random` - Get random XKCD comic
  - [x] `xkcd specific` - Get specific XKCD comic

## Guild Management

### config.py - Guild Configuration

- [ ] `config` (group command)
  - [ ] `config logs` (subgroup)
    - [ ] `config logs set` - Set log channel
    - [ ] `config logs get` - Get log channel
  - [ ] `config channels` (subgroup)
    - [ ] `config channels set` - Set channel configuration
    - [ ] `config channels get` - Get channel configuration
  - [ ] `config perms` (subgroup)
    - [ ] `config perms set` - Set permission configuration
    - [ ] `config perms get` - Get permission configuration
  - [ ] `config roles` (subgroup)
    - [ ] `config roles set` - Set role configuration
    - [ ] `config roles get` - Get role configuration
  - [ ] `config prefix` (subgroup)
    - [ ] `config prefix set` - Set custom prefix
    - [ ] `config prefix clear` - Clear custom prefix

### setup.py - Guild Setup

- [ ] `setup` (group command)
  - [ ] `setup jail` - Setup jail system

## Info Commands

### avatar.py - Avatar Display

- [x] `avatar` - Display user avatar (hybrid)

### info.py - Information Commands

- [ ] `info` (group command)
  - [ ] `info server` - Server information
  - [ ] `info member` - Member information
  - [ ] `info roles` - Role information
  - [ ] `info emotes` - Server emotes

### membercount.py - Member Count

- [x] `membercount` - Show server member count

## Levels System

### level.py - Individual Level

- [ ] `level` - Show user level

### levels.py - Level Management

- [ ] `levels` (group command)
  - [ ] `levels set` - Set user level
  - [ ] `levels setxp` - Set user XP
  - [ ] `levels reset` - Reset user level
  - [ ] `levels blacklist` - Blacklist user from levels

## Moderation Commands

### ban.py - Ban Commands

- [ ] `ban` - Ban a user

### cases.py - Moderation Cases

- [ ] `cases` (group command)
  - [ ] `cases view` - View moderation case
  - [ ] `cases modify` - Modify moderation case

### clearafk.py - Clear AFK

- [ ] `clearafk` - Clear AFK status
- [ ] `clear_afk` - Alternative command

### jail.py - Jail System

- [ ] `jail` - Jail a user

### kick.py - Kick Commands

- [ ] `kick` - Kick a user

### pollban.py - Poll Ban

- [ ] `pollban` - Ban from polls
- [ ] `poll_ban` - Alternative command

### pollunban.py - Poll Unban

- [ ] `pollunban` - Unban from polls
- [ ] `poll_unban` - Alternative command

### purge.py - Message Purging

- [ ] `purge` - Purge messages (hybrid)
- [ ] `slash_purge` - Slash command version
- [ ] `prefix_purge` - Prefix command version

### report.py - Report System

- [ ] `report` - Report a user/message

### slowmode.py - Slowmode

- [ ] `slowmode` - Set channel slowmode

### snippetban.py - Snippet Ban

- [ ] `snippetban` - Ban from snippets
- [ ] `snippet_ban` - Alternative command

### snippetunban.py - Snippet Unban

- [ ] `snippetunban` - Unban from snippets
- [ ] `snippet_unban` - Alternative command

### tempban.py - Temporary Ban

- [ ] `tempban` - Temporarily ban a user

### timeout.py - Timeout Commands

- [ ] `timeout` - Timeout a user

### unban.py - Unban Commands

- [ ] `unban` - Unban a user

### unjail.py - Unjail Commands

- [ ] `unjail` - Unjail a user

### untimeout.py - Remove Timeout

- [ ] `untimeout` - Remove user timeout

### warn.py - Warning System

- [ ] `warn` - Warn a user

## Services (Background/Event Handlers)

### bookmarks.py - Bookmark System

- [ ] Event handlers for bookmark reactions

### gif_limiter.py - GIF Limiting

- [ ] Event handlers for GIF limiting

### influxdblogger.py - InfluxDB Logging

- [ ] Event handlers for InfluxDB logging

### levels.py - Level Tracking

- [ ] Event handlers for XP/level tracking

### starboard.py - Starboard System

- [ ] `starboard` (group command)
  - [ ] `starboard setup` - Setup starboard
  - [ ] `starboard remove` - Remove starboard
- [ ] Event handlers for starboard reactions

### status_roles.py - Status Roles

- [ ] Event handlers for status-based role assignment

### temp_vc.py - Temporary Voice Channels

- [ ] Event handlers for temporary voice channels

### tty_roles.py - TTY Role Management

- [ ] Event handlers for TTY role management

## Snippet Management

### create_snippet.py - Create Snippets

- [ ] `createsnippet` - Create a snippet
- [ ] `create_snippet` - Alternative command

### delete_snippet.py - Delete Snippets

- [ ] `deletesnippet` - Delete a snippet
- [ ] `delete_snippet` - Alternative command

### edit_snippet.py - Edit Snippets

- [ ] `editsnippet` - Edit a snippet
- [ ] `edit_snippet` - Alternative command

### get_snippet.py - Retrieve Snippets

- [ ] `snippet` - Get a snippet

### get_snippet_info.py - Snippet Information

- [ ] `snippetinfo` - Get snippet information
- [ ] `snippet_info` - Alternative command

### list_snippets.py - List Snippets

- [ ] `snippets` - List all snippets
- [ ] `list_snippets` - Alternative command

### toggle_snippet_lock.py - Toggle Snippet Lock

- [ ] `togglesnippetlock` - Toggle snippet lock
- [ ] `toggle_snippet_lock` - Alternative command

## Tools

### tldr.py - TLDR Pages

- [ ] `tldr` - Get TLDR page (hybrid)
- [ ] `slash_tldr` - Slash command version
- [ ] `prefix_tldr` - Prefix command version

### wolfram.py - Wolfram Alpha

- [ ] `wolfram` - Query Wolfram Alpha

## Utility Commands

### afk.py - AFK System

- [ ] `afk` - Set AFK status
- [ ] `permafk` - Set permanent AFK

### encode_decode.py - Encoding/Decoding

- [ ] `encode` - Encode text
- [ ] `decode` - Decode text

### ping.py - Ping/Latency

- [ ] `ping` - Show bot latency

### poll.py - Poll Creation

- [ ] `poll` - Create a poll

### remindme.py - Reminders

- [ ] `remindme` - Set a reminder

### run.py - Code Execution

- [ ] `run` - Execute code
- [ ] `languages` - List supported languages

### self_timeout.py - Self Timeout

- [ ] `self_timeout` - Timeout yourself

### timezones.py - Timezone Commands

- [ ] `timezones` - Timezone utilities

### wiki.py - Wikipedia Search

- [ ] `wiki` (group command)
  - [ ] `wiki arch` - Search Arch Wiki
  - [ ] `wiki atl` - Search ATL Wiki

---

**Total Commands:** 120+
**Completed:** 0/120+

**Testing Notes:**

- Test both slash commands and traditional prefix commands where applicable
- Verify permission checks work correctly for each command
- Test error handling and edge cases
- Check embed formatting and responses
- Validate database operations where applicable
- Test group commands and their subcommands
- Verify aliases work correctly
- Test event handlers in services modules
