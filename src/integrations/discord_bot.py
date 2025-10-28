import discord
from discord.ext import commands
from src.agent.agent_core import FoodieAgent
from src.database.connection import db_manager
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
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="food recommendations 🍕"
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
                    for chunk in chunks:
                        await message.channel.send(chunk)
            
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await message.reply("Maaf, terjadi kesalahan. Coba lagi ya! 😅")


def setup_commands(bot: FoodieDiscordBot):
    """Setup bot commands"""
    
    @bot.command(name="help", aliases=["bantuan"])
    async def help_command(ctx):
        """Show help message"""
        embed = discord.Embed(
            title="🍕 FoodieBot - Asisten Rekomendasi Makanan",
            description="Aku bantu kamu cari makanan yang pas! Chat langsung atau mention aku.",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="💬 Cara Pakai",
            value=(
                "• DM aku langsung, atau\n"
                "• Mention aku di channel: @FoodieBot pesan kamu\n"
                "• Ceritain budget, lokasi, atau mood kamu!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="✨ Fitur",
            value=(
                "• Rekomendasi berdasarkan budget, lokasi, mood\n"
                "• Info lengkap restoran & menu\n"
                "• Simpan favorit\n"
                "• Track riwayat pesanan"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Contoh",
            value=(
                '`"Lagi laper, budget 50rb daerah Kemang"`\n'
                '`"Lagi happy, mau dessert enak"`\n'
                '`"Cari resto romantis buat date"`'
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Commands",
            value=(
                "`!help` - Bantuan\n"
                "`!reset` - Reset conversation\n"
                "`!profile` - Lihat profil kamu\n"
                "`!ping` - Cek bot status"
            ),
            inline=False
        )
        
        embed.set_footer(text="Dibuat dengan ❤️ untuk pecinta kuliner")
        
        await ctx.send(embed=embed)
    
    @bot.command(name="reset")
    async def reset_command(ctx):
        """Reset conversation history"""
        response = bot.agent.reset_conversation(str(ctx.author.id))
        await ctx.send(response)
    
    @bot.command(name="profile", aliases=["profil"])
    async def profile_command(ctx):
        """Show user profile"""
        user_info = bot.agent.get_user_info(str(ctx.author.id))
        
        embed = discord.Embed(
            title=f"👤 Profil {ctx.author.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Budget Default",
            value=f"Rp {user_info.get('default_budget', 0):,}",
            inline=True
        )
        
        embed.add_field(
            name="Lokasi Default",
            value=user_info.get('default_location', 'Belum diset'),
            inline=True
        )
        
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
    
    @bot.command(name="ping")
    async def ping_command(ctx):
        """Check bot latency"""
        latency = round(bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")
    
    @bot.command(name="about", aliases=["tentang"])
    async def about_command(ctx):
        """About the bot"""
        embed = discord.Embed(
            title="🤖 Tentang FoodieBot",
            description=(
                "FoodieBot adalah AI agent yang membantu kamu menemukan "
                "makanan yang pas berdasarkan budget, lokasi, mood, dan preferensi kamu!"
            ),
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🧠 Powered by",
            value="Groq API (Llama 3.1 70B)",
            inline=True
        )
        
        embed.add_field(
            name="💾 Database",
            value="PostgreSQL",
            inline=True
        )
        
        embed.add_field(
            name="📚 Features",
            value="Recommendation • Favorites • History • Smart Search",
            inline=False
        )
        
        await ctx.send(embed=embed)


def run_discord_bot():
    """Initialize and run Discord bot"""
    try:
        # Initialize database
        db_manager.initialize()
        db_manager.create_tables()
        logger.info("Database initialized")
        
        # Create bot instance
        bot = FoodieDiscordBot()
        
        # Setup commands
        setup_commands(bot)
        
        # Run bot
        logger.info("Starting Discord bot...")
        bot.run(Config.DISCORD_BOT_TOKEN)
    
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")
        raise
    finally:
        db_manager.close()


if __name__ == "__main__":
    run_discord_bot()
