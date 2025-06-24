"""
Study‑oriented commands for the Discord bot
"""
import re
import logging
import discord
from discord.ext import commands
import asyncio

logger = logging.getLogger(__name__)

class StudyCommands(commands.Cog):
    """AI‑powered study helpers (quiz, explain, convert, formula, math)"""
    CHAR_LIMIT = 2000  # Discord hard limit per message

    def __init__(self, bot: commands.Bot):
        self.bot = bot               # gives us bot.sarvam_client

    # ---------- helpers ----------

    async def _ask_sarvam(self, prompt: str) -> str:
        """
        Send a one‑turn prompt to Sarvam and return its reply.
        Falls back to an error message on failure.
        """
        try:
            reply = await self.bot.sarvam_client.generate_response(
                [{"role": "user", "content": prompt}]
            )
            return reply or "🤖 Sorry, no response right now."
        except Exception as exc:
            logger.error("Sarvam error: %s", exc)
            return f"⚠️ Sarvam error: {exc}"

    async def _send_long(self, ctx: commands.Context, text: str):
        """Split very long replies so they stay under 2 000 characters, breaking on whitespace/newlines."""
        for chunk in self.split_message_by_limit(text, self.CHAR_LIMIT):
            await ctx.send(chunk)

    def split_message_by_limit(text, limit=2000):
        """Split text into chunks <= limit, breaking on whitespace/newlines."""
        import re
        parts = []
        while len(text) > limit:
            # Find last whitespace/newline before limit
            idx = max(text.rfind("\n", 0, limit), text.rfind(" ", 0, limit))
            if idx == -1:
                idx = limit
            parts.append(text[:idx].rstrip())
            text = text[idx:].lstrip()
        if text:
            parts.append(text)
        return parts

    # ---------- commands ----------

    @commands.command(name="notes")
    async def notes_command(self, ctx: commands.Context, *, subject: str):
        """Generate AI-powered study notes for <subject>."""
        async with ctx.typing():
            prompt = f"Write concise, high-yield study notes on '{subject}'. Use bullet points if possible."
            reply = await self._ask_sarvam(prompt)
        embed = discord.Embed(
            title=f"📝 Study Notes: {subject}",
            description=reply,
            color=discord.Color.blue(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="codehelper")
    async def codehelper_command(self, ctx: commands.Context, *, code: str):
        """Explain code step-by-step using Sarvam AI."""
        async with ctx.typing():
            prompt = f"Explain the following code step-by-step, in simple terms.\n\n{code}"
            reply = await self._ask_sarvam(prompt)
        embed = discord.Embed(
            title="💻 Code Helper",
            description=reply,
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="roast")
    async def roast_command(self, ctx: commands.Context, user: discord.Member = None):
        """Roast a user with a funny AI-powered insult."""
        if user is None:
            await ctx.send("Please mention a user to roast!")
            return
        async with ctx.typing():
            prompt = f"Roast {user.display_name} with a funny, light-hearted insult. Keep it safe for work."
            reply = await self._ask_sarvam(prompt)
        embed = discord.Embed(
            title=f"🔥 Roast for {user.display_name}",
            description=reply,
            color=discord.Color.red(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="explain")
    async def explain_command(self, ctx: commands.Context, *, concept: str):
        """Explain <concept> in simple, high‑school‑level language."""
        async with ctx.typing():
            prompt = f"Explain the concept '{concept}' in clear, simple terms."
            reply = await self._ask_sarvam(prompt)

        embed = discord.Embed(
            title=f"📚 Explain: {concept}",
            description=reply,
            color=discord.Color.green(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="convert")
    async def convert_command(self, ctx: commands.Context, *, query: str):
        """Unit conversion. Format: !convert 5 km to miles"""
        match = re.search(r"([\\d\\.]+)\\s*([a-zA-Zµ/]+)\\s+to\\s+([a-zA-Zµ/]+)", query)
        if not match:
            return await ctx.send(
                "Use `!convert <value> <unit> to <unit>` (e.g. `!convert 5 km to miles`)."
            )

        value, src, dest = match.groups()
        async with ctx.typing():
            prompt = f"Convert {value} {src} to {dest}. Provide only the numeric result (rounded if sensible) followed by the unit."
            reply = await self._ask_sarvam(prompt)

        embed = discord.Embed(
            title="🔄 Unit Conversion",
            description=f"{value} {src} → **{reply}**",
            color=discord.Color.orange(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="formula")
    async def formula_command(self, ctx: commands.Context, *, topic: str):
        """List the key formulas for <topic>."""
        async with ctx.typing():
            prompt = (
                f"List the most important formulas for '{topic}'. "
                "Put each formula on its own bullet line."
            )
            reply = await self._ask_sarvam(prompt)

        embed = discord.Embed(
            title=f"📐 Formulas: {topic}",
            description=reply,
            color=discord.Color.gold(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="meaning")
    async def meaning_command(self, ctx: commands.Context, *, name: str = None):
        """Get the meaning and origin of a given name."""
        if not name or not name.strip():
            await ctx.send("❗ Please provide a name. Usage: `!meaning <name>`")
            return
        async with ctx.typing():
            prompt = f"What is the meaning and origin of the name '{name}'?"
            reply = await self._ask_sarvam(prompt)
        embed = discord.Embed(
            title=f"🔤 Meaning of {name}",
            description=reply,
            color=discord.Color.purple(),
        )
        await ctx.send(embed=embed)

    @commands.command(name="reply")
    async def reply_command(self, ctx: commands.Context, *, message: str):
        """Reply to the bot and maintain short-term context for a conversation."""
        if not hasattr(self.bot, "_sarvam_context"):
            self.bot._sarvam_context = []
        # Keep last 5 exchanges
        context = self.bot._sarvam_context[-8:] if hasattr(self.bot, "_sarvam_context") else []
        context.append({"role": "user", "content": message})
        async with ctx.typing():
            response = await self.bot.sarvam_client.generate_response(context)
        context.append({"role": "assistant", "content": response})
        self.bot._sarvam_context = context[-8:]  # keep only last 8 turns
        await ctx.send(response or "🤖 Sorry, I couldn't generate a response right now.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Only process replies to the bot, not DMs or bot messages
        if message.author.bot or not message.reference:
            return
        ref = message.reference
        if not ref.resolved:
            try:
                ref_msg = await message.channel.fetch_message(ref.message_id)
            except Exception:
                return
        else:
            ref_msg = ref.resolved
        # Only respond if the replied-to message is from the bot
        if not ref_msg or not ref_msg.author or not ref_msg.author.bot:
            return
        # Maintain short-term context for the conversation
        if not hasattr(self.bot, "_sarvam_context"):  # global context
            self.bot._sarvam_context = []
        # Add the previous bot message as context
        self.bot._sarvam_context.append({"role": "assistant", "content": ref_msg.content})
        self.bot._sarvam_context.append({"role": "user", "content": message.content})
        # Only keep last 8 turns
        self.bot._sarvam_context = self.bot._sarvam_context[-8:]
        async with message.channel.typing():
            response = await self.bot.sarvam_client.generate_response(self.bot._sarvam_context)
        self.bot._sarvam_context.append({"role": "assistant", "content": response})
        self.bot._sarvam_context = self.bot._sarvam_context[-8:]
        await message.channel.send(response, reference=message)

# ---------- cog setup helper ----------

def setup(bot: commands.Bot):
    bot.add_cog(StudyCommands(bot))
# This function is called by the bot to load this cog