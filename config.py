"""
Discord Security Bot v2.0 - Configuration
Created by: spice.efx
Advanced configuration management with environment variable support
"""

import os

class BotConfig:
    """Configuration class for the Discord Security Bot"""
    
    # Bot settings
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    
    # Approval system settings
    APPROVAL_TIMEOUT = int(os.getenv('APPROVAL_TIMEOUT', '10'))  # seconds
    
    # Target role ID for notifications
    TARGET_ROLE_ID = int(os.getenv('TARGET_ROLE_ID', '1266706345571258390'))
    
    # Role-based permissions
    MODERATOR_ROLES = [
        role.strip() for role in 
        os.getenv('MODERATOR_ROLES', 'Moderator,Admin,Administrator,Mod').split(',')
    ]
    
    # Required permissions for moderators
    MODERATOR_PERMISSIONS = [
        'kick_members',
        'ban_members',
        'manage_messages',
        'manage_guild'
    ]
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'bot.log')
    
    # Bot permissions required
    REQUIRED_BOT_PERMISSIONS = [
        'send_messages',
        'read_messages',
        'kick_members',
        'view_audit_log',
        'add_reactions',
        'read_message_history'
    ]
    
    @classmethod
    def get_moderator_roles(cls):
        """Get list of moderator role names"""
        return cls.MODERATOR_ROLES
        
    @classmethod
    def is_valid_timeout(cls, timeout):
        """Validate timeout value"""
        return 5 <= timeout <= 300  # Between 5 seconds and 5 minutes
        
    @classmethod
    def get_required_permissions(cls):
        """Get list of required bot permissions"""
        return cls.REQUIRED_BOT_PERMISSIONS
