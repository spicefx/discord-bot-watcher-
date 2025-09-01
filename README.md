# Discord Security Bot v2.0
*Created by: **spice.efx***

An advanced Discord security bot with comprehensive PostgreSQL logging that automatically monitors for new bot additions and implements a sophisticated approval system with role-based permissions.

## Features

- 🤖 **Auto-detects new bots** joining your server
- 📨 **Sends DM notifications** to users with specific role
- ⏰ **10-second approval timeout** - auto-kicks if no response
- ✅❌ **React to approve/reject** bots instantly
- 🛡️ **Role-based permissions** - only specified role can manage bots
- 📊 **Advanced PostgreSQL logging** - tracks all bot actions
- 🔍 **Comprehensive audit trails** - who invited bots, when, and why
- 📈 **Detailed statistics** - view historical data and trends
- 🚨 **Real-time monitoring** with status commands

## Quick Setup

### 1. Install Dependencies
```bash
pip install discord.py python-dotenv
```

### 2. Configure Your Bot Token
- Copy `.env.example` to `.env`
- Add your Discord bot token to the `.env` file:
```
DISCORD_BOT_TOKEN=your_actual_bot_token_here
```

### 3. Set Target Role (Optional)
If you want to change the target role ID from the default, update in `.env`:
```
TARGET_ROLE_ID=your_role_id_here
```

### 4. Run the Bot
```bash
python main.py
```

## Discord Bot Permissions Required

Your bot needs these permissions in Discord:
- ✅ **Kick Members** (essential for auto-kick feature)
- ✅ Send Messages
- ✅ Read Message History
- ✅ Add Reactions
- ✅ View Audit Log

## How It Works

1. **Detection**: Bot joins your server → Security bot detects it
2. **Notification**: DMs sent to users with target role ID `1266706345571258390`
3. **Approval**: Users click ✅ to approve or ❌ to reject
4. **Auto-kick**: If no response within 10 seconds, bot is automatically kicked

## Commands (for users with target role)

- `!botstatus` - View pending approvals and statistics
- `!approve <bot_id>` - Manually approve a specific bot
- `!reject <bot_id>` - Manually reject a specific bot
- `!logs [limit]` - View comprehensive bot action logs with statistics
- `!bothistory <bot_id>` - View complete history for a specific bot

## Configuration Options

Edit `.env` file to customize:
- `DISCORD_BOT_TOKEN` - Your bot's token
- `TARGET_ROLE_ID` - Role ID that receives notifications (default: 1266706345571258390)
- `APPROVAL_TIMEOUT` - Seconds to wait before auto-kick (default: 10)
- `COMMAND_PREFIX` - Bot command prefix (default: !)

## Files Structure

- `main.py` - Entry point and bot startup
- `bot_fixed.py` - Main bot logic and event handlers with advanced features
- `database.py` - PostgreSQL database operations and logging
- `config.py` - Configuration settings
- `utils.py` - Helper functions and security utilities
- `.env.example` - Environment variables template

## Credits

**Creator:** spice.efx  
**Version:** 2.0  
**License:** Custom Discord Security Bot

This advanced security bot includes comprehensive PostgreSQL logging, audit trails, and sophisticated bot management features designed for enterprise-level Discord server protection.

## Troubleshooting

**Bot not kicking:**
- Ensure bot has "Kick Members" permission
- Check bot's role is higher than the bots it needs to kick

**Commands not working:**
- Verify user has the target role ID
- Check command prefix is correct (default: !)

**No DM notifications:**
- Confirm target role ID exists in your server
- Ensure users allow DMs from server members