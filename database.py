"""
Discord Security Bot v2.0 - Database Management
Created by: spice.efx
Advanced PostgreSQL database operations for comprehensive bot action logging
and security audit trails
"""

import os
import asyncio
import asyncpg
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class BotDatabase:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = os.getenv('DATABASE_URL')
        
    async def initialize(self):
        """Initialize database connection and create tables"""
        if not self.database_url:
            logger.error("DATABASE_URL not found in environment variables")
            return False
            
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            await self.create_tables()
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
            
    async def create_tables(self):
        """Create necessary tables for logging"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bot_actions (
                    id SERIAL PRIMARY KEY,
                    action_type VARCHAR(20) NOT NULL,
                    bot_id BIGINT NOT NULL,
                    bot_name VARCHAR(255) NOT NULL,
                    guild_id BIGINT NOT NULL,
                    guild_name VARCHAR(255) NOT NULL,
                    moderator_id BIGINT,
                    moderator_name VARCHAR(255),
                    invited_by_id BIGINT,
                    invited_by_name VARCHAR(255),
                    reason TEXT,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    bot_permissions BIGINT,
                    account_age_days INTEGER
                )
            ''')
            
            # Create index for faster queries
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_bot_actions_guild_timestamp 
                ON bot_actions(guild_id, timestamp DESC)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_bot_actions_bot_id 
                ON bot_actions(bot_id)
            ''')
            
    async def log_bot_action(self, action_data: Dict):
        """Log a bot action to the database"""
        if not self.pool:
            logger.warning("Database not initialized, cannot log action")
            return
            
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO bot_actions (
                        action_type, bot_id, bot_name, guild_id, guild_name,
                        moderator_id, moderator_name, invited_by_id, invited_by_name,
                        reason, bot_permissions, account_age_days
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ''', 
                action_data.get('action_type'),
                action_data.get('bot_id'),
                action_data.get('bot_name'),
                action_data.get('guild_id'),
                action_data.get('guild_name'),
                action_data.get('moderator_id'),
                action_data.get('moderator_name'),
                action_data.get('invited_by_id'),
                action_data.get('invited_by_name'),
                action_data.get('reason'),
                action_data.get('bot_permissions'),
                action_data.get('account_age_days')
                )
        except Exception as e:
            logger.error(f"Failed to log bot action: {e}")
            
    async def get_recent_logs(self, guild_id: int, limit: int = 20) -> List[Dict]:
        """Get recent bot actions for a guild"""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT * FROM bot_actions 
                    WHERE guild_id = $1 
                    ORDER BY timestamp DESC 
                    LIMIT $2
                ''', guild_id, limit)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get recent logs: {e}")
            return []
            
    async def get_bot_history(self, bot_id: int) -> List[Dict]:
        """Get action history for a specific bot"""
        if not self.pool:
            return []
            
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT * FROM bot_actions 
                    WHERE bot_id = $1 
                    ORDER BY timestamp DESC
                ''', bot_id)
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get bot history: {e}")
            return []
            
    async def get_stats(self, guild_id: int) -> Dict:
        """Get statistics for bot actions in a guild"""
        if not self.pool:
            return {}
            
        try:
            async with self.pool.acquire() as conn:
                # Get total counts
                stats = await conn.fetchrow('''
                    SELECT 
                        COUNT(*) as total_actions,
                        COUNT(*) FILTER (WHERE action_type = 'approved') as approved_count,
                        COUNT(*) FILTER (WHERE action_type = 'rejected') as rejected_count,
                        COUNT(*) FILTER (WHERE action_type = 'auto_kicked') as auto_kicked_count,
                        COUNT(*) FILTER (WHERE action_type = 'detected') as detected_count
                    FROM bot_actions 
                    WHERE guild_id = $1
                ''', guild_id)
                
                # Get recent activity (last 24 hours)
                recent_stats = await conn.fetchrow('''
                    SELECT 
                        COUNT(*) as recent_total,
                        COUNT(*) FILTER (WHERE action_type = 'approved') as recent_approved,
                        COUNT(*) FILTER (WHERE action_type = 'rejected') as recent_rejected,
                        COUNT(*) FILTER (WHERE action_type = 'auto_kicked') as recent_auto_kicked
                    FROM bot_actions 
                    WHERE guild_id = $1 AND timestamp > NOW() - INTERVAL '24 hours'
                ''', guild_id)
                
                return {
                    'total_actions': stats['total_actions'] or 0,
                    'approved_count': stats['approved_count'] or 0,
                    'rejected_count': stats['rejected_count'] or 0,
                    'auto_kicked_count': stats['auto_kicked_count'] or 0,
                    'detected_count': stats['detected_count'] or 0,
                    'recent_total': recent_stats['recent_total'] or 0,
                    'recent_approved': recent_stats['recent_approved'] or 0,
                    'recent_rejected': recent_stats['recent_rejected'] or 0,
                    'recent_auto_kicked': recent_stats['recent_auto_kicked'] or 0
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
            
    async def close(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()

# Global database instance
db = BotDatabase()