# Guild Onboarding Guide

Complete guide to setting up Tux for your Discord server, including automated onboarding and manual configuration options.

## Overview

Tux includes a comprehensive onboarding system that automatically sets up essential features when the bot joins your server. The system guides server administrators through configuration with an interactive setup wizard and provides ongoing status tracking.

## Automated Setup (When Bot Joins)

When Tux joins your server, it automatically:

1. **Creates Permission Ranks** - Sets up a standard 8-tier permission hierarchy
2. **Creates Setup Channel** - Makes a dedicated `#tux-setup` channel for onboarding
3. **Sends Interactive Welcome** - Posts a comprehensive setup guide with a start button
4. **Initializes Database** - Prepares your server for full functionality

### Dedicated Setup Channel

Tux creates a special `#tux-setup` channel that serves as your onboarding hub:

- **📍 Location**: Automatically appears in your channel list
- **🎯 Purpose**: Guided setup experience with interactive buttons
- **📊 Progress Dashboard**: Becomes a status channel showing ongoing progress
- **🔒 Permissions**: Everyone can read, only admins can start setup
- **📌 Persistent**: Channel remains after setup for reference and status updates

### Default Permission Hierarchy

```text
Rank 0: Member - Basic server member access
Rank 1: Trusted - Enhanced trust level
Rank 2: Junior Moderator - Can warn, timeout, jail
Rank 3: Moderator - Can kick and ban
Rank 4: Senior Moderator - Advanced moderation tools
Rank 5: Administrator - Server administration
Rank 6: Head Administrator - Full server control
Rank 7: Server Owner - Complete access
```

## Interactive Setup Wizard

The setup wizard guides you through essential configuration in minutes.

### Launching the Wizard

**From the dedicated channel:**

- Click the **"🚀 Start Setup Wizard"** button in `#tux-setup`

**Using commands:**

```bash
# Slash command (recommended)
/setup wizard

# Prefix command
$setup wizard
```

### Setup Steps

#### 1. Welcome & Introduction

- Overview of what will be configured
- Estimated completion time (3-5 minutes)

#### 2. Permission System Check

- Verifies default permission ranks are created
- Shows current permission hierarchy

#### 3. Log Channel Setup

- Configure channels for moderation logging
- Auto-suggests existing channels by name
- Sets up: Mod logs, Audit logs, Private logs, Join logs, Report logs, Dev logs

#### 4. Staff Role Assignment

- Assign Discord roles to permission ranks
- Examples: @Moderator → Rank 3, @Admin → Rank 5

#### 5. Command Protection

- Set permission requirements for sensitive commands
- Protects: ban, kick, timeout, config, eval

#### 6. Completion & Summary

- Shows setup completion status
- Provides next steps and additional resources

## Manual Configuration Options

### Permission Management

#### Initialize Permission Ranks

```bash
/config permission init
```

#### Create Custom Permission Ranks

```bash
/config permission create 8 "Super Admin" "Ultimate access"
/config permission create 10 "Custom Role" "Special permissions"
```

#### Assign Roles to Ranks

```bash
/config role assign 3 @Moderator
/config role assign 5 @Admin
/config role assign 2 @Helper
```

#### Protect Commands

```bash
/config command set ban 3 moderation
/config command set kick 3 moderation
/config command set config 5 admin
/config command set eval 7 owner
```

### Log Channel Configuration

#### Set Log Channels

```bash
# Open interactive log channel selector
/config logs

# Or use individual commands
/config logs mod set #mod-logs
/config logs audit set #audit-logs
/config logs private set #private-logs
```

## Setup Status & Verification

### Check Setup Progress

```bash
/setup status
```

This command shows:

- ✅ Permission ranks initialized
- ✅ Log channels configured
- ✅ Staff roles assigned
- ✅ Essential commands protected

### Setup Completion Percentage

The status command displays overall completion (e.g., "4/4 steps completed (100%)").

## Advanced Configuration

### Configuration File Setup

For self-hosted instances, you can pre-configure settings using a config file:

```yaml
# config.yml
guilds:
  123456789012345678:  # Guild ID
    permissions:
      ranks:
        - rank: 0
          name: "Member"
          description: "Basic access"
        - rank: 3
          name: "Moderator"
          description: "Full moderation"
      assignments:
        - rank: 3
          role_id: 987654321098765432
      commands:
        - command: "ban"
          rank: 3
        - command: "kick"
          rank: 3
    channels:
      mod_log: 111222333444555666
      audit_log: 777888999000111222
      general: 333444555666777888
```

### Bulk Operations

#### Assign Multiple Roles at Once

```bash
# Use multiple assignment commands
/config role assign 2 @TrialMod
/config role assign 3 @Moderator
/config role assign 4 @SeniorMod
/config role assign 5 @Admin
```

#### Batch Command Protection

```bash
# Protect multiple moderation commands
/config command set ban 3
/config command set kick 3
/config command set timeout 2
/config command set warn 1
```

## Troubleshooting

### Common Issues

#### "Permission ranks not initialized"

```bash
# Run initialization
/config permission init
```

#### "No log channels configured"

```bash
# Use the interactive setup
/setup wizard

# Or manually configure
/config logs
```

#### "Commands not protected"

```bash
# Check current permissions
/config command list

# Set protections
/config command set ban 3
/config command set kick 3
```

### Reset and Start Over

**⚠️ This action cannot be undone and will reset all guild configuration.**

```bash
/setup reset
```

## Best Practices

### Permission Hierarchy

1. **Start Simple** - Begin with basic ranks (Member, Moderator, Admin, Owner)
2. **Scale Gradually** - Add intermediate ranks as your server grows
3. **Role Mapping** - Map Discord roles directly to permission ranks
4. **Regular Review** - Audit permissions quarterly

### Log Channel Organization

1. **Separate Concerns** - Use different channels for different log types
2. **Staff Access** - Ensure staff can view but not edit log channels
3. **Archive Old Logs** - Set up automated log archival
4. **Monitor Activity** - Regularly review moderation logs

### Command Protection

1. **Principle of Least Privilege** - Give minimum required access
2. **Critical Commands First** - Protect ban, kick, and config commands immediately
3. **Test Permissions** - Verify protections work as expected
4. **Document Changes** - Keep records of permission changes

## Integration with Existing Servers

### Migrating from Other Bots

1. **Export Current Settings** - Document existing permissions and roles
2. **Map Equivalent Ranks** - Create Tux ranks matching your current hierarchy
3. **Test Gradually** - Enable features incrementally
4. **Staff Training** - Ensure staff understand new command structure

### Large Server Considerations

1. **Plan Permission Structure** - Design hierarchy before implementation
2. **Bulk Role Assignment** - Use multiple assignment commands efficiently
3. **Channel Categories** - Organize log channels in dedicated categories
4. **Staff Communication** - Announce changes and provide training

## Support & Resources

### Getting Help

```bash
# View all commands
/help

# Check setup status
/setup status

# View configuration
/config
```

### Community Resources

- **Documentation**: Full command reference and guides
- **Support Server**: Community assistance and troubleshooting
- **GitHub Issues**: Bug reports and feature requests

### Configuration Backup

```bash
# View complete configuration
/config

# Export settings (future feature)
/config export
```

This onboarding system ensures new servers are operational quickly while providing the flexibility for advanced customization as servers grow.
