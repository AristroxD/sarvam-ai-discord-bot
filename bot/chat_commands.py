"""
Fun and entertainment commands for the Discord bot
"""

import asyncio
import random
import logging
from typing import List, Dict, Any
import discord
from discord.ext import commands
from bot.store import ChatChannelMemory
channel_memory = ChatChannelMemory()


logger = logging.getLogger(__name__)

class FunCommands(commands.Cog):
    """Fun and entertainment commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_games: Dict[int, Dict[str, Any]] = {}
        
    @commands.command(name="joke")
    async def joke_command(self, ctx: commands.Context):
        """Tell a random joke from the free joke API"""
        import aiohttp
        url = "https://official-joke-api.appspot.com/random_joke"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    joke = f"{data['setup']}\n{data['punchline']}"
                else:
                    joke = "Couldn't fetch a joke right now. Try again later!"
        embed = discord.Embed(
            title="😂 Random Joke",
            description=joke,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="fun")
    async def fun_command(self, ctx: commands.Context):
        """Random fun activities"""
        activities = [
            "🎲 Roll a dice: You got a **{}**!",
            "🪙 Flip a coin: It's **{}**!",
            "🌟 Your luck today: **{}**/10",
            "🎯 Random fact: Did you know that honey never spoils?",
            "🎯 Random fact: A group of flamingos is called a 'flamboyance'!",
            "🎯 Random fact: Octopuses have three hearts!",
            "🔮 Magic 8-Ball says: **{}**"
        ]
        
        activity = random.choice(activities)
        
        if "dice" in activity:
            result = activity.format(random.randint(1, 6))
        elif "coin" in activity:
            result = activity.format(random.choice(["Heads", "Tails"]))
        elif "luck" in activity:
            result = activity.format(random.randint(1, 10))
        elif "Magic 8-Ball" in activity:
            responses = ["Yes", "No", "Maybe", "Ask again later", "Definitely", "Not likely", "Absolutely"]
            result = activity.format(random.choice(responses))
        else:
            result = activity
        
        embed = discord.Embed(
            title="🎉 Fun Activity",
            description=result,
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="game")
    async def game_command(self, ctx: commands.Context, game_type: str = None):
        """Start a mini-game"""
        if not game_type:
            embed = discord.Embed(
                title="🎮 Available Games",
                description="Use `!game <type>` to start:\n\n"
                          "• `trivia` - Answer trivia questions\n"
                          "• `math` - Solve math problems\n"
                          "• `word` - Word association game\n"
                          "• `riddle` - Solve riddles",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
            return
        
        if game_type.lower() == "trivia":
            await self.start_trivia(ctx)
        elif game_type.lower() == "math":
            await self.start_math_game(ctx)
        elif game_type.lower() == "word":
            await self.start_word_game(ctx)
        elif game_type.lower() == "riddle":
            await self.start_riddle_game(ctx)
        else:
            await ctx.send("Unknown game type! Use `!game` to see available games.")
    
    async def start_trivia(self, ctx: commands.Context):
        """Start a trivia game"""
        questions = [
            {"q": "What is the capital of France?", "a": "paris"},
            {"q": "What is 2 + 2?", "a": "4"},
            {"q": "What planet is known as the Red Planet?", "a": "mars"},
            {"q": "Who painted the Mona Lisa?", "a": "leonardo da vinci"},
            {"q": "What is the largest ocean on Earth?", "a": "pacific"}
        ]
        
        question = random.choice(questions)
        
        embed = discord.Embed(
            title="🧠 Trivia Question",
            description=f"**{question['q']}**\n\nYou have 30 seconds to answer!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        try:
            answer = await self.bot.wait_for('message', timeout=30.0, check=check)
            if answer.content.lower().strip() == question['a']:
                await ctx.send("🎉 Correct! Well done!")
            else:
                await ctx.send(f"❌ Wrong! The answer was: **{question['a']}**")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Time's up! The answer was: **{question['a']}**")
    
    async def start_math_game(self, ctx: commands.Context):
        """Start a math game"""
        num1 = random.randint(1, 50)
        num2 = random.randint(1, 50)
        operation = random.choice(['+', '-', '*'])
        
        if operation == '+':
            answer = num1 + num2
        elif operation == '-':
            answer = num1 - num2
        else:  # multiplication
            answer = num1 * num2
        
        embed = discord.Embed(
            title="🔢 Math Challenge",
            description=f"**{num1} {operation} {num2} = ?**\n\nYou have 30 seconds!",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        try:
            user_answer = await self.bot.wait_for('message', timeout=30.0, check=check)
            if user_answer.content.strip() == str(answer):
                await ctx.send("🎉 Correct! Great math skills!")
            else:
                await ctx.send(f"❌ Wrong! The answer was: **{answer}**")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Time's up! The answer was: **{answer}**")
    
    async def start_word_game(self, ctx: commands.Context):
        """Start a word association game"""
        words = ["cat", "sun", "book", "music", "ocean", "mountain", "flower", "computer", "friendship", "adventure"]
        word = random.choice(words)
        
        embed = discord.Embed(
            title="💭 Word Association",
            description=f"Give me a word that relates to: **{word}**\n\nBe creative!",
            color=discord.Color.teal()
        )
        await ctx.send(embed=embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        try:
            response = await self.bot.wait_for('message', timeout=30.0, check=check)
            await ctx.send(f"Nice association! **{word}** → **{response.content}** 🌟")
        except asyncio.TimeoutError:
            await ctx.send("⏰ Time's up! Maybe next time!")
    
    async def start_riddle_game(self, ctx: commands.Context):
        """Start a riddle game"""
        riddles = [
            {"q": "I speak without a mouth and hear without ears. I have no body, but come alive with wind. What am I?", "a": "echo"},
            {"q": "The more you take, the more you leave behind. What am I?", "a": "footsteps"},
            {"q": "I'm tall when I'm young, and short when I'm old. What am I?", "a": "candle"},
            {"q": "What has keys but no locks, space but no room, and you can enter but not go inside?", "a": "keyboard"},
            {"q": "What gets wetter as it dries?", "a": "towel"}
        ]
        
        riddle = random.choice(riddles)
        
        embed = discord.Embed(
            title="🤔 Riddle Time",
            description=f"**{riddle['q']}**\n\nYou have 60 seconds to think!",
            color=discord.Color.purple()
        )
        await ctx.send(embed=embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        try:
            answer = await self.bot.wait_for('message', timeout=60.0, check=check)
            if riddle['a'].lower() in answer.content.lower():
                await ctx.send("🎉 Excellent! You solved the riddle!")
            else:
                await ctx.send(f"❌ Good try! The answer was: **{riddle['a']}**")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Time's up! The answer was: **{riddle['a']}**")
    
    @commands.command(name="guess")
    async def guess_command(self, ctx: commands.Context, max_num: int = 100):
        """Start a number guessing game"""
        if max_num < 10 or max_num > 1000:
            await ctx.send("Please choose a number between 10 and 1000!")
            return
        
        secret_number = random.randint(1, max_num)
        attempts = 0
        max_attempts = min(10, max_num // 10 + 3)
        
        embed = discord.Embed(
            title="🎯 Number Guessing Game",
            description=f"I'm thinking of a number between 1 and {max_num}!\n"
                       f"You have {max_attempts} attempts. Good luck!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        
        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel
        
        while attempts < max_attempts:
            try:
                guess_msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                
                try:
                    guess = int(guess_msg.content.strip())
                except ValueError:
                    await ctx.send("Please enter a valid number!")
                    continue
                
                attempts += 1
                
                if guess == secret_number:
                    await ctx.send(f"🎉 Congratulations! You guessed it in {attempts} attempts!")
                    return
                elif guess < secret_number:
                    remaining = max_attempts - attempts
                    await ctx.send(f"📈 Too low! {remaining} attempts remaining.")
                else:
                    remaining = max_attempts - attempts
                    await ctx.send(f"📉 Too high! {remaining} attempts remaining.")
                
                if attempts >= max_attempts:
                    await ctx.send(f"💔 Game over! The number was **{secret_number}**")
                    return
                    
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ Time's up! The number was **{secret_number}**")
                return
    
    @commands.command(name="roll")
    async def roll_command(self, ctx: commands.Context, sides: int = 6):
        """Roll a dice with specified sides"""
        if sides < 2 or sides > 100:
            await ctx.send("Please choose between 2 and 100 sides!")
            return
        
        result = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"Rolling a {sides}-sided die...\n\n**Result: {result}**",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name="flip")
    async def flip_command(self, ctx: commands.Context):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        emoji = "🟡" if result == "Heads" else "⚫"
        
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"Flipping a coin...\n\n{emoji} **{result}**",
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
    
    
    @commands.command(name="ask")
    async def ask_command(self, ctx: commands.Context, *, question: str):
        """Ask the Sarvam AI a question"""
        async with ctx.typing():
            context = [
                {"role": "user", "content": question}
            ]

            response = await self.bot.sarvam_client.generate_response(context)

            if response and response.strip():
                # Send in 2000-character chunks
                chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send("🤖 Sorry, I couldn't generate a response right now.")

    @commands.command(name="info")
    async def info_command(self, ctx: commands.Context):
        """Show bot info and credits"""
        embed = discord.Embed(
            title="🤖 Bot Info & Credits",
            description="A fun and intelligent Discord bot powered by **Sarvam AI** and developed by **Team Thinkron**.",
            color=discord.Color.purple()
        )

        # Bot Information
        embed.add_field(name="📌 Prefix", value=self.bot.command_prefix, inline=True)
        embed.add_field(name="👑 Owner", value=f"<@{self.bot.config.admin_user_id}>", inline=True)
        embed.add_field(name="🔗 Source Code", value="[GitHub](https://github.com/teamthinkron)", inline=True)

        # Team Thinkron
        embed.add_field(
            name="🚀 Team Thinkron",
            value=(
                "A passionate collective of developers, creators, and AI enthusiasts. "
                "Building open, smart, and fun tools for the future."
            ),
            inline=False
        )

        # Sarvam AI Details
        embed.add_field(
            name="🧠 Powered by Sarvam AI",
            value=(
                "**Model:** Sarvam Ultra v1\n"
                "**Capabilities:** Conversational AI, Contextual Memory, GPT-style responses\n"
                "**Use Case:** Fast, responsive Discord bot integration"
            ),
            inline=False
        )

        # Support & Help
        embed.add_field(
            name="🆘 Support Server",
            value="[Join our support server](https://discord.gg/k7Sss4yKj5)",
            inline=True
        )

        embed.add_field(
            name="📣 Need Help?",
            value="Use `!help` to see all available commands.",
            inline=True
        )

        # Footer and timestamp
        embed.set_footer(text="Built with ❤️ by Team Thinkron • Powered by Sarvam AI")
        embed.timestamp = ctx.message.created_at

        await ctx.send(embed=embed)


    @commands.command(name="ping")
    async def ping_command(self, ctx: commands.Context):
        """Check bot latency"""
        await ctx.send(f"🏓 Pong! Latency: {round(self.bot.latency * 1000)} ms")

    @commands.command(name="setprefix")
    @commands.has_permissions(administrator=True)
    async def set_prefix(self, ctx: commands.Context, new_prefix: str):
        """Change the bot's command prefix (Server Admin only)"""
        if len(new_prefix) > 5:
            await ctx.send("Prefix must be 5 characters or less!")
            return
        old_prefix = self.bot.config.command_prefix
        self.bot.config.command_prefix = new_prefix
        self.bot.command_prefix = new_prefix
        embed = discord.Embed(
            title="✅ Prefix Updated",
            description=f"Command prefix changed from `{old_prefix}` to `{new_prefix}`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="setchannel")
    @commands.has_permissions(administrator=True)
    async def set_channel(self, ctx):
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        channel_memory.set_channel(guild_id, channel_id)
        await ctx.send("✅ This channel is now the AI chat channel.")

    @commands.command(name="unsetchannel")
    @commands.has_permissions(administrator=True)
    async def unset_channel(self, ctx):
        guild_id = ctx.guild.id
        channel_memory.remove_channel(guild_id)
        await ctx.send("❌ Removed AI chat channel setting.")


    @commands.command(name="summarize")
    async def summarize_command(self, ctx: commands.Context, *, text_or_link: str):
        """Summarizes a long passage or webpage into key points (stub)"""
        embed = discord.Embed(
            title="📝 Summarize",
            description="This feature is coming soon!",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)

    @commands.command(name="define")
    async def define_command(self, ctx: commands.Context, *, word: str):
        """Returns the definition and usage of a word using Sarvam AI"""
        async with ctx.typing():
            prompt = f"Define the word '{word}' and provide an example sentence."
            context = [
                {"role": "user", "content": prompt}
            ]
            response = await self.bot.sarvam_client.generate_response(context)
            embed = discord.Embed(
                title=f"📖 Definition: {word}",
                description=response or "Sorry, I couldn't find a definition.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @commands.command(name="quote")
    async def quote_command(self, ctx: commands.Context):
        """Sends a random motivational or thought-provoking quote using Sarvam AI"""
        async with ctx.typing():
            prompt = "Give me a short, motivational or thought-provoking quote."
            context = [
                {"role": "user", "content": prompt}
            ]
            response = await self.bot.sarvam_client.generate_response(context)
            embed = discord.Embed(
                title="💡 Quote",
                description=response or "Sorry, I couldn't fetch a quote right now.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context):
        """Show help for all commands, including admin if user is an admin"""
        is_admin = ctx.author.guild_permissions.administrator

        embed = discord.Embed(
            title="📘 AI Discord Bot Help",
            description="Here's a list of everything I can do. Use the prefix `!` before each command.",
            color=discord.Color.blurple()
        )

        # General Commands
        embed.add_field(name="🎉 General Commands", value="\u200b", inline=False)
        embed.add_field(name="`!help`", value="Show this help message", inline=True)
        embed.add_field(name="`!ask <question>`", value="Ask Sarvam AI something", inline=True)
        embed.add_field(name="`!define <word>`", value="Look up the definition of a word", inline=True)
        embed.add_field(name="`!quote`", value="Get a random inspirational quote", inline=True)
        embed.add_field(name="`!stats`", value="Show bot/server statistics", inline=True)
        embed.add_field(name="`!info`", value="Show bot info", inline=True)
        embed.add_field(name="`/ping`", value="Check bot latency", inline=True)

        # Fun Commands
        embed.add_field(name="\n🎮 Fun & Games", value="\u200b", inline=False)
        embed.add_field(name="`!joke`", value="Get a random joke", inline=True)
        embed.add_field(name="`!fun`", value="Random fun activities", inline=True)
        embed.add_field(name="`!game`", value="Start a mini-game", inline=True)
        embed.add_field(name="`!guess`", value="Play number guessing", inline=True)
        embed.add_field(name="`!roll`", value="Roll a dice", inline=True)
        embed.add_field(name="`!flip`", value="Flip a coin", inline=True)

        # Admin-only section (only shown to admins)
        if is_admin:
            embed.add_field(name="\n🛡️ Admin Commands", value="\u200b", inline=False)
            embed.add_field(name="`!setchannel [#channel]`", value="Set the bot’s chat channel", inline=True)
            embed.add_field(name="`!unsetchannel`", value="Unset the fixed channel", inline=True)
            embed.add_field(name="`!setprefix <prefix>`", value="Change the bot prefix", inline=True)

        embed.set_footer(text="Use responsibly. AI remembers what you teach it. 🤖")

        await ctx.send(embed=embed)

    @commands.command(name="stats")
    async def stats_command(self, ctx: commands.Context):
        """Show bot/server statistics"""
        import platform
        import datetime
        import discord

        embed = discord.Embed(
            title="📊 Bot & Server Stats",
            color=discord.Color.green()
        )

        # Server info
        embed.add_field(name="Server Name", value=ctx.guild.name if ctx.guild else "DM", inline=True)
        embed.add_field(name="Server ID", value=ctx.guild.id if ctx.guild else "DM", inline=True)
        embed.add_field(name="Member Count", value=ctx.guild.member_count if ctx.guild else "DM", inline=True)
        embed.add_field(name="Your ID", value=ctx.author.id, inline=True)

        # Bot performance
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        embed.add_field(name="System", value=platform.system(), inline=True)

        await ctx.send(embed=embed)