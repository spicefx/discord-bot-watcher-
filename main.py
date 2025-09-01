#!/usr/bin/env python3
"""
Discord Security Bot v2.0 - Main Entry Point
Created by: spice.efx
Monitors for new bot additions and implements comprehensive approval system
with PostgreSQL logging and advanced security features
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from bot_fixed import SecurityBot, setup_commands

# Load environment variables
load_dotenv()

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )

async def main():
    """Main entry point for the Discord security bot"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Get bot token from environment
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN environment variable not found!")
        logger.error("Please set your Discord bot token in the environment or .env file")
        return
    
    # Create and run the bot
    bot = SecurityBot()
    
    # Setup commands
    setup_commands(bot)
    
    try:
        logger.info("Starting Discord Security Bot...")
        await bot.start(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
