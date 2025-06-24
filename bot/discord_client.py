import logging
import asyncio
import random
from typing import Optional
import io
import textwrap

import discord
from discord.ext import commands

from bot.config import BotConfig
from bot.sarvam_client import SarvamClient
from bot.chat_manager import ChatManager
from bot.store import ChatChannelMemory

# ---------------------------------------------------------------------------
# Long‑message handling helpers
# ---------------------------------------------------------------------------

MAX_DISCORD_LEN = 2_000  # Discord hard limit per message
FILE_THRESHOLD = 8_000   # send as a file once we go above this many characters

channel_memory = ChatChannelMemory()
logger = logging.getLogger(__name__)

async def _safe_send(channel: discord.TextChannel, content: str, *, wrap_in_code: bool = False) -> None:
    """Send arbitrarily long text safely without splitting words or code blocks."""
    # 1️⃣  If the reply is extremely long, upload as a text file instead of spamming dozens of messages
    if len(content) > FILE_THRESHOLD:
        fp = io.StringIO(content)
        await channel.send(
            "⚡ The reply is huge, so I'm uploading it as **response.txt** instead:",
            file=discord.File(fp, filename="response.txt"),
        )
        return

    # 2️⃣  Otherwise stream it out, making sure each chunk is ≤ 2000 chars *including* code fences
    prefix = "```" if wrap_in_code else ""
    suffix = "```" if wrap_in_code else ""
    effective_limit = MAX_DISCORD_LEN - len(prefix) - len(suffix)

    for chunk in textwrap.wrap(
        content,
        width=effective_limit,
        break_long_words=False,
        break_on_hyphens=False,
        replace_whitespace=False,
    ):
        await channel.send(f"{prefix}{chunk}{suffix}")


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
            help_command=None,
        )

        self.config = config
        self.chat_manager = ChatManager(config.max_history_messages)
        self.sarvam_client = sarvam_client

    # ---------------------------------------------------------------------
    # life‑cycle events
    # ---------------------------------------------------------------------

    async def setup_hook(self):
        logger.info("Setting up Discord bot…")

        from bot.chat_commands import FunCommands
        from bot.study_commands import StudyCommands
        await self.add_cog(FunCommands(self))
        await self.add_cog(StudyCommands(self))

        logger.info("Discord bot setup complete")

    async def close(self):
        await super().close()

    async def on_ready(self):
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Bot is in {len(self.guilds)} guilds")

        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{self.config.command_prefix}help | AI Chat Bot",
        )
        await self.change_presence(activity=activity)

        logger.info(
            f"Memory‑enabled chat channels: {channel_memory.all_channels()}"
        )

    # ---------------------------------------------------------------------
    # message handling
    # ---------------------------------------------------------------------

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # let command processors run first
        await self.process_commands(message)

        # ignore messages that start with the prefix (handled by commands)
        if message.content.startswith(self.config.command_prefix):
            return

        should_respond = await self._should_respond_to_message(message)
        if should_respond:
            await self._handle_chat_message(message)

    async def _should_respond_to_message(self, message: discord.Message) -> bool:
        if isinstance(message.channel, discord.DMChannel):
            return True

        return channel_memory.is_channel_allowed(
            message.channel.id
        ) or (self.user in message.mentions)

    async def _handle_chat_message(self, message: discord.Message):
        try:
            async with message.channel.typing():
                # lightweight random reaction
                if (
                    self.config.enable_auto_reactions
                    and random.random() < 0.1
                ):
                    reactions = ["👍", "😊", "🤔", "💡", "❤️", "🎉"]
                    try:
                        await message.add_reaction(random.choice(reactions))
                    except Exception:
                        pass

                # store the user message in history
                self.chat_manager.add_message(
                    channel_id=message.channel.id,
                    user_id=message.author.id,
                    content=message.content,
                    role="user",
                )

                # choose history context: per‑user for DMs, per‑channel for guilds
                if isinstance(message.channel, discord.DMChannel):
                    context = self.chat_manager.get_conversation_context(
                        user_id=message.author.id
                    )
                else:
                    context = self.chat_manager.get_conversation_context(
                        channel_id=message.channel.id
                    )

                # get the AI reply
                response = await self.sarvam_client.generate_response(context)

                if response:
                    # determine if it *looks* like code → wrap in fences
                    is_code = response.lstrip().startswith(
                        ("```", "def ", "class ")
                    )
                    await _safe_send(
                        message.channel, response, wrap_in_code=is_code
                    )

                    # store assistant response in history
                    self.chat_manager.add_message(
                        channel_id=message.channel.id,
                        user_id=self.user.id,
                        content=response,
                        role="assistant",
                    )
                    logger.info(
                        f"Responded to message from {message.author} in {message.channel}"
                    )
                else:
                    await message.channel.send(
                        "Sorry, I couldn't generate a response right now. Please try again."
                    )

        except Exception:
            logger.exception("Error handling message")
            await message.channel.send(
                "Sorry, I encountered an error while processing your message."
            )


