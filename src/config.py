import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Groq API
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    
    # Discord
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    DISCORD_COMMAND_PREFIX = os.getenv("DISCORD_COMMAND_PREFIX", "!")
    
    # Weather API (OpenWeatherMap - Free)
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/foodiebot.log")
    
    # Agent Settings
    MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
    RESPONSE_TIMEOUT = int(os.getenv("RESPONSE_TIMEOUT", "30"))
    
    # Default Location for Weather
    DEFAULT_LOCATION = os.getenv("DEFAULT_LOCATION", "Jakarta")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = [
            ("GROQ_API_KEY", cls.GROQ_API_KEY),
            ("DISCORD_BOT_TOKEN", cls.DISCORD_BOT_TOKEN),
        ]
        
        missing = [name for name, value in required if not value]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Weather API is optional but recommended
        if not cls.WEATHER_API_KEY:
            print("⚠️  Warning: WEATHER_API_KEY not set. Weather features will be disabled.")
        
        return True