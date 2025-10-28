#!/usr/bin/env python3
"""
FoodieBot - Food Recommendation Agent
Main entry point for the application
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
        print("=" * 60)
        print("🍕 FoodieBot - AI Food Recommendation Agent")
        print("=" * 60)
        print(f"Model: {Config.GROQ_MODEL}")
        print(f"Database: {Config.DATABASE_URL.split('@')[1] if '@' in Config.DATABASE_URL else 'Local'}")
        print("=" * 60)
        print()
        
        # Start Discord bot
        logger.info("Starting FoodieBot...")
        run_discord_bot()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n❌ Configuration Error: {e}")
        print("\nMake sure you have created a .env file with all required variables.")
        print("Check .env.example for reference.")
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
