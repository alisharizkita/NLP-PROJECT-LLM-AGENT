import discord
from discord.ext import commands
from src.agent.agent_core import FoodieAgent
from src.config import Config
import logging

logger = logging.getLogger(__name__)

class FoodieDiscordBot(commands.Bot):
    """Discord bot for FoodieBot agent"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=Config.DISCORD_COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.agent = FoodieAgent()
        logger.info("Discord bot initialized")
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Bot logged in as {self.user.name} ({self.user.id})")
        print(f"✅ FoodieBot is online as {self.user.name}!")
        print(f"📊 Ready to serve food recommendations!")
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="food recommendations 🍕 | !help"
            )
        )
    
    async def on_message(self, message: discord.Message):
        """Handle incoming messages"""
        # Ignore bot's own messages
        if message.author == self.user:
            return
        
        # Only respond to DMs or mentions
        if not isinstance(message.channel, discord.DMChannel) and not self.user.mentioned_in(message):
            return
        
        # Process commands first
        await self.process_commands(message)
        
        # If it's a command, don't process as regular message
        ctx = await self.get_context(message)
        if ctx.valid:
            return
        
        # Extract message content (remove mention if exists)
        content = message.content
        if self.user.mentioned_in(message):
            content = content.replace(f"<@{self.user.id}>", "").strip()
        
        if not content:
            return
        
        # Show typing indicator
        async with message.channel.typing():
            try:
                # Process message through agent
                response = self.agent.process_message(
                    discord_id=str(message.author.id),
                    username=message.author.name,
                    message=content
                )
                
                # Send response (split if too long)
                if len(response) <= 2000:
                    await message.reply(response)
                else:
                    # Split long messages
                    chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            await message.channel.send(chunk)
            
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await message.reply("Maaf, terjadi kesalahan. Coba lagi ya! 😅")


def setup_commands(bot: FoodieDiscordBot):
    """Setup bot commands"""
    
    @bot.command(name="help", aliases=["bantuan", "h"])
    async def help_command(ctx):
        """Show help message"""
        embed = discord.Embed(
            title="🍕 FoodieBot - Your Food Companion!",
            description="Aku bantu kamu cari makanan yang pas! Chat langsung atau mention aku.",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="💬 Cara Pakai",
            value=(
                "• **DM aku langsung**, atau\n"
                "• **Mention** aku di channel: `@FoodieBot pesan kamu`\n"
                "• Ceritain budget, lokasi, mood, atau cuaca!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="✨ Aku Bisa Bantu:",
            value=(
                "🍽️ Rekomendasi makanan (budget, mood, cuaca)\n"
                "📝 Resep masakan & tips memasak\n"
                "📊 Hitung kalori makanan\n"
                "🌤️ Saran makanan sesuai cuaca\n"
                "💡 Nutrition advice & diet tips\n"
                "🗺️ Info kuliner daerah"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Contoh Chat:",
            value=(
                '`"Budget 30rb mau makan enak"`\n'
                '`"Lagi hujan, cocoknya makan apa?"`\n'
                '`"Kalori nasi goreng berapa?"`\n'
                '`"Resep ayam goreng crispy dong"`\n'
                '`"Lagi diet, rekomendasi makanan?"`'
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Commands",
            value=(
                "`!help` - Tampilkan menu ini\n"
                "`!reset` - Reset conversation\n"
                "`!stats` - Lihat statistik chat kamu\n"
                "`!ping` - Cek bot status\n"
                "`!about` - Tentang FoodieBot"
            ),
            inline=False
        )
        
        embed.set_footer(text="Dibuat dengan ❤️ untuk pecinta kuliner | Powered by Groq AI")
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        
        await ctx.send(embed=embed)
    
    @bot.command(name="reset")
    async def reset_command(ctx):
        """Reset conversation history"""
        response = bot.agent.reset_conversation(str(ctx.author.id))
        await ctx.send(f"🔄 {response}")
    
    @bot.command(name="stats", aliases=["statistik"])
    async def stats_command(ctx):
        """Show user statistics"""
        stats = bot.agent.get_conversation_stats(str(ctx.author.id))
        
        embed = discord.Embed(
            title=f"📊 Statistik Chat {ctx.author.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Total Pesan",
            value=f"{stats['total_messages']} pesan",
            inline=True
        )
        
        embed.add_field(
            name="Pesan Kamu",
            value=f"{stats['user_messages']} pesan",
            inline=True
        )
        
        embed.add_field(
            name="Pesan Bot",
            value=f"{stats['bot_messages']} pesan",
            inline=True
        )
        
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.set_footer(text="Data disimpan selama bot online")
        
        await ctx.send(embed=embed)
    
    @bot.command(name="ping")
    async def ping_command(ctx):
        """Check bot latency"""
        latency = round(bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: **{latency}ms**",
            color=discord.Color.green()
        )
        
        # Add active users count
        active_users = bot.agent.get_active_users_count()
        embed.add_field(
            name="Active Users",
            value=f"{active_users} users",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @bot.command(name="about", aliases=["tentang", "info"])
    async def about_command(ctx):
        """About the bot"""
        embed = discord.Embed(
            title="🤖 Tentang FoodieBot",
            description=(
                "FoodieBot adalah AI-powered food companion yang membantu kamu "
                "menemukan makanan yang pas dengan budget, mood, dan cuaca kamu!"
            ),
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🧠 AI Model",
            value="Groq API - Llama 3.1 70B",
            inline=True
        )
        
        embed.add_field(
            name="🌤️ Weather Data",
            value="OpenWeatherMap API",
            inline=True
        )
        
        embed.add_field(
            name="💾 Storage",
            value="In-Memory (session-based)",
            inline=True
        )
        
        embed.add_field(
            name="✨ Special Features",
            value=(
                "• Conversation memory\n"
                "• Weather-aware recommendations\n"
                "• Calorie calculator\n"
                "• Mood-based suggestions\n"
                "• Recipe knowledge"
            ),
            inline=False
        )
        
        embed.add_field(
            name="👨‍💻 Developer",
            value="[Your Name] - NLP Project",
            inline=False
        )
        
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        embed.set_footer(text="Made with ❤️ | Open Source")
        
        await ctx.send(embed=embed)
    
    @bot.command(name="weather", aliases=["cuaca"])
    async def weather_command(ctx, *, location: str = None):
        """Check weather (manual command)"""
        if not location:
            location = Config.DEFAULT_LOCATION
        
        # Use agent to get weather
        message = f"Bagaimana cuaca di {location}?"
        response = bot.agent.process_message(
            str(ctx.author.id),
            ctx.author.name,
            message
        )
        
        await ctx.send(response)


def run_discord_bot():
    """Initialize and run Discord bot"""
    try:
        # Create bot instance
        bot = FoodieDiscordBot()
        
        # Setup commands
        setup_commands(bot)
        
        # Run bot
        logger.info("Starting Discord bot...")
        print("\n🚀 Starting FoodieBot...")
        print("="*60)
        bot.run(Config.DISCORD_BOT_TOKEN)
    
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")
        raise


if __name__ == "__main__":
    run_discord_bot()