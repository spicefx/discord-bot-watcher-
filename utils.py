"""
Discord Security Bot v2.0 - Utility Functions
Created by: spice.efx
Advanced helper functions for permissions, secure messaging, and validation
"""

import logging
import discord
from typing import List, Optional
from config import BotConfig

logger = logging.getLogger(__name__)

def is_moderator(member: discord.Member) -> bool:
    """
    Check if a member has the specific target role
    
    Args:
        member: Discord member to check
        
    Returns:
        bool: True if member has the target role
    """
    if not member:
        return False
    
    # Check if member has the specific target role
    target_role_id = BotConfig.TARGET_ROLE_ID
    target_role = member.guild.get_role(target_role_id)
    
    if target_role and target_role in member.roles:
        return True
        
    # Fallback: Check if member has administrator permission
    if member.guild_permissions.administrator:
        return True
        
    return False

async def send_safe_dm(user: discord.User, **kwargs) -> Optional[discord.Message]:
    """
    Safely send a DM to a user with error handling
    
    Args:
        user: Discord user to send DM to
        **kwargs: Arguments to pass to send()
        
    Returns:
        Optional[discord.Message]: Sent message or None if failed
    """
    try:
        return await user.send(**kwargs)
    except discord.Forbidden:
        logger.warning(f"Cannot send DM to {user.name} - DMs disabled or blocked")
        return None
    except discord.HTTPException as e:
        logger.error(f"HTTP error sending DM to {user.name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error sending DM to {user.name}: {e}")
        return None

def format_countdown(seconds: int) -> str:
    """
    Format countdown timer for display
    
    Args:
        seconds: Number of seconds remaining
        
    Returns:
        str: Formatted countdown string
    """
    if seconds <= 0:
        return "⏰ Time's up!"
    elif seconds == 1:
        return "⏰ 1 second remaining"
    else:
        return f"⏰ {seconds} seconds remaining"

def format_bot_info(bot_member: discord.Member) -> dict:
    """
    Format bot information for display
    
    Args:
        bot_member: Discord bot member
        
    Returns:
        dict: Formatted bot information
    """
    return {
        'name': bot_member.name,
        'id': bot_member.id,
        'discriminator': bot_member.discriminator,
        'created_at': bot_member.created_at,
        'joined_at': bot_member.joined_at,
        'avatar_url': str(bot_member.display_avatar.url),
        'guild': bot_member.guild.name,
        'guild_id': bot_member.guild.id
    }

def validate_bot_permissions(bot_member: discord.Member, required_perms: List[str]) -> tuple[bool, List[str]]:
    """
    Validate that the bot has required permissions
    
    Args:
        bot_member: Bot member to check
        required_perms: List of required permission names
        
    Returns:
        tuple[bool, List[str]]: (has_all_perms, missing_perms)
    """
    bot_perms = bot_member.guild_permissions
    missing_perms = []
    
    for perm_name in required_perms:
        if not hasattr(bot_perms, perm_name):
            logger.warning(f"Unknown permission: {perm_name}")
            continue
            
        if not getattr(bot_perms, perm_name):
            missing_perms.append(perm_name)
            
    return len(missing_perms) == 0, missing_perms

def create_audit_log_entry(action: str, bot_member: discord.Member, moderator: discord.User, reason: str | None = None) -> dict:
    """
    Create an audit log entry for bot actions
    
    Args:
        action: Action taken (approved, rejected, kicked)
        bot_member: Bot member involved
        moderator: Moderator who took action
        reason: Optional reason for action
        
    Returns:
        dict: Audit log entry
    """
    from datetime import datetime, timezone
    
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'action': action,
        'bot_id': bot_member.id,
        'bot_name': bot_member.name,
        'guild_id': bot_member.guild.id,
        'guild_name': bot_member.guild.name,
        'moderator_id': moderator.id,
        'moderator_name': moderator.name,
        'reason': reason or 'No reason provided'
    }

def get_bot_invite_info(bot_member: discord.Member) -> Optional[dict]:
    """
    Get information about how the bot was invited (if available)
    
    Args:
        bot_member: Bot member to check
        
    Returns:
        Optional[dict]: Invite information or None
    """
    try:
        # This would require audit log access and recent invite checking
        # Placeholder for invite tracking functionality
        return {
            'invited_by': 'Unknown',
            'invite_code': 'Unknown',
            'permissions': str(bot_member.guild_permissions.value)
        }
    except Exception as e:
        logger.error(f"Error getting invite info for {bot_member.name}: {e}")
        return None

async def check_bot_safety(bot_member: discord.Member) -> dict:
    """
    Perform basic safety checks on a bot
    
    Args:
        bot_member: Bot member to check
        
    Returns:
        dict: Safety check results
    """
    safety_info = {
        'is_verified': bot_member.public_flags.verified_bot if hasattr(bot_member.public_flags, 'verified_bot') else False,
        'account_age_days': (discord.utils.utcnow() - bot_member.created_at).days,
        'has_avatar': bot_member.avatar is not None,
        'permissions_value': bot_member.guild_permissions.value,
        'dangerous_permissions': []
    }
    
    # Check for potentially dangerous permissions
    dangerous_perms = [
        'administrator',
        'manage_guild',
        'manage_roles',
        'manage_channels',
        'kick_members',
        'ban_members',
        'manage_webhooks'
    ]
    
    bot_perms = bot_member.guild_permissions
    for perm in dangerous_perms:
        if hasattr(bot_perms, perm) and getattr(bot_perms, perm):
            safety_info['dangerous_permissions'].append(perm)
            
    return safety_info
