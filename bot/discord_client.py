"""
Discord bot client with AI chat integration (Sarvam AI Edition)
"""
import logging
import asyncio
import random
from typing import Optional
import discord
from discord.ext import commands

from bot.config import BotConfig
from bot.sarvam_client import SarvamClient
from bot.chat_manager import ChatManager
from bot.store import ChatChannelMemory

channel_memory = ChatChannelMemory()
logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    """Discord bot with AI chat capabilities"""
    
    def __init__(self, config: BotConfig, sarvam_client: SarvamClient):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.guild_messages = True

        super().__init__(
            command_prefix=config.command_prefix,
            intents=intents,
            help_command=None
        )
        
        self.config = config
        self.chat_manager = ChatManager(config.max_history_messages)
        self.sarvam_client = sarvam_client

    async def setup_hook(self):
        logger.info("Setting up Discord bot...")

        from bot.chat_commands import FunCommands
        await self.add_cog(FunCommands(self))

        logger.info("Discord bot setup complete")

    async def close(self):
        await super().close()

    async def on_ready(self):
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Bot is in {len(self.guilds)} guilds")

        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{self.config.command_prefix}help | AI Chat Bot"
        )
        await self.change_presence(activity=activity)

        logger.info(f"Memory-enabled chat channels: {channel_memory.all_channels()}")

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        await self.process_commands(message)

        if message.content.startswith(self.config.command_prefix):
            return

        should_respond = await self._should_respond_to_message(message)
        if should_respond:
            await self._handle_chat_message(message)

    async def _should_respond_to_message(self, message: discord.Message) -> bool:
        if isinstance(message.channel, discord.DMChannel):
            return True

        return channel_memory.is_channel_allowed(message.channel.id) or (self.user in message.mentions)

    async def _handle_chat_message(self, message: discord.Message):
        try:
            async with message.channel.typing():
                if self.config.enable_auto_reactions and random.random() < 0.1:
                    reactions = ["👍", "😊", "🤔", "💡", "❤️", "🎉"]
                    try:
                        await message.add_reaction(random.choice(reactions))
                    except:
                        pass

                self.chat_manager.add_message(
                    channel_id=message.channel.id,
                    user_id=message.author.id,
                    content=message.content,
                    role="user"
                )

                if isinstance(message.channel, discord.DMChannel):
                    context = self.chat_manager.get_conversation_context(user_id=message.author.id)
                else:
                    context = self.chat_manager.get_conversation_context(channel_id=message.channel.id)

                response = await self.sarvam_client.generate_response(context)

                if response:
                    if len(response) > 2000:
                        chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                        for chunk in chunks:
                            await message.channel.send(chunk)
                    else:
                        await message.channel.send(response)

                    self.chat_manager.add_message(
                        channel_id=message.channel.id,
                        user_id=self.user.id,
                        content=response,
                        role="assistant"
                    )

                    logger.info(f"Responded to message from {message.author} in {message.channel}")
                else:
                    await message.channel.send("Sorry, I couldn't generate a response right now. Please try again.")

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await message.channel.send("Sorry, I encountered an error while processing your message.")

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error(f"Command error in {ctx.command}: {error}")
        await ctx.send(f"An error occurred: {str(error)}")