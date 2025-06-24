# Discord Sarvam AI Chatbot
# A Discord bot that integrates with Sarvam AI for enhanced chat capabilities.
# This bot allows users to interact with Sarvam AI, manage chat channels, and provides fun commands.
# 
# This file is part of the Discord Sarvam AI Chatbot project.
# 
# Licensed under the GNU General Public License v3.0 (GPL-3.0).
# See LICENSE file for details.

"""
Discord Sarvam AI Chatbot
A Discord bot that integrates with Sarvam AI for enhanced chat capabilities.
This bot allows users to interact with Sarvam AI, manage chat channels, and provides fun commands.
"""
import sys
import asyncio
import logging
import os
from dotenv import load_dotenv
from bot.discord_client import DiscordBot
from bot.config import BotConfig
from bot.sarvam_client import SarvamClient
from bot.discord_client import DiscordBot
from bot.store import ChatChannelMemory


if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to start the Discord bot"""
    try:
        # Initialize configuration
        config = BotConfig()

        # Validate required environment variables
        if not config.discord_token:
            logger.error("DISCORD_TOKEN environment variable is required")
            return

        if not config.sarvam_api_key:
            logger.error("SARVAM_API_KEY environment variable is required")
            return

        logger.info("Starting Discord Sarvam AI Chatbot...")

        # Initialize Sarvam client
        sarvam_client = SarvamClient(config)

        # Initialize and start the bot
        bot = DiscordBot(config, sarvam_client)
        await bot.start(config.discord_token)

    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot shutting down...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")