# Overview

This is a Discord Security Bot designed to monitor and manage bot additions to Discord servers. The bot automatically detects when new bots join a server and implements an approval system that requires moderator intervention within a specified timeout period. If no approval is given within the timeout, the bot is automatically removed from the server. The system includes role-based permissions, safe messaging utilities, and comprehensive logging.

# User Preferences

Preferred communication style: Simple, everyday language.

Target Role ID: 1266706345571258390 - Only users with this specific role should receive bot notifications and can approve/reject bots.

Recent Enhancement: Added comprehensive logging system with PostgreSQL database to track all bot actions, who invited bots, and approval/rejection history.

# System Architecture

## Core Components

**Bot Detection System**: The main bot class (`SecurityBot`) extends Discord.py's `commands.Bot` and uses event handlers to monitor member joins. It specifically filters for bot accounts and initiates the approval workflow when detected.

**Approval Workflow**: Implements a timeout-based approval system where detected bots are tracked in a pending state. Each pending bot has an associated asyncio task that handles the countdown and automatic removal if not approved by moderators within the configured timeout period.

**Permission System**: Role-based authorization system that identifies moderators through multiple criteria:
- Administrator permissions
- Specific Discord permissions (kick, ban, manage messages, manage guild)
- Configurable role names

**State Management**: Uses in-memory data structures to track:
- Pending bots awaiting approval (Dict mapping bot IDs to guild info and tasks)
- Approved bots (Set of approved bot IDs)
- Moderator notification status

**Configuration Management**: Environment-variable driven configuration system supporting:
- Approval timeout periods
- Moderator role definitions
- Command prefixes
- Logging levels
- Required bot permissions

**Error Handling**: Implements safe messaging utilities with built-in error handling for DM delivery and user interactions.

## Design Patterns

**Event-Driven Architecture**: Uses Discord.py's event system for real-time bot detection and member management.

**Task-Based Concurrency**: Leverages asyncio tasks for handling timeout periods and concurrent approval workflows across multiple servers.

**Configuration Pattern**: Centralized configuration class with environment variable support and sensible defaults.

**Utility Pattern**: Separated utility functions for common operations like permission checking and safe messaging.

# External Dependencies

**Discord API**: Primary integration through Discord.py library for bot functionality, event handling, and server management.

**Python dotenv**: Environment variable management for configuration loading.

**Python asyncio**: Built-in library for asynchronous programming and task management.

**Python logging**: Built-in logging system for application monitoring and debugging.

The bot requires specific Discord permissions including send_messages, kick_members, view_audit_log, and read_message_history to function properly.