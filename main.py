#!/usr/bin/env python3
"""
FoodieBot - AI Food Recommendation Agent
Pure LLM with Weather API Integration
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.utils.logger import setup_logger
from src.integrations.discord_bot import run_discord_bot
import logging

def main():
    """Main application entry point"""
    
    # Setup logger
    logger = setup_logger()
    
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")
        
        # Print startup banner
        print("\n" + "="*60)
        print("🍕 FoodieBot - AI Food Recommendation Agent")
        print("="*60)
        print(f"🧠 Model: {Config.GROQ_MODEL}")
        print(f"💾 Storage: In-Memory (session-based)")
        print(f"🌤️  Weather: {'Enabled' if Config.WEATHER_API_KEY else 'Disabled'}")
        print("="*60)
        print()
        
        # Start Discord bot
        logger.info("Starting FoodieBot...")
        run_discord_bot()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}")
        print("\n💡 Tips:")
        print("1. Make sure you have created a .env file")
        print("2. Check .env.example for required variables")
        print("3. Get Groq API key at: https://console.groq.com")
        print("4. Get Discord token at: https://discord.com/developers")
        print("5. Get Weather API key at: https://openweathermap.org/api (optional)")
        sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        print("\n\n👋 FoodieBot shutting down. Goodbye!")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()