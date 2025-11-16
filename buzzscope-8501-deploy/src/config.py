"""
Configuration management for BuzzScope
"""
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for BuzzScope application"""
    
    # API Keys
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT', 'BuzzScope/1.0')
    DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    # Data Storage
    DATA_DIR = os.getenv('DATA_DIR', './data')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Platform-specific settings
    PLATFORMS = {
        'hackernews': {
            'api_url': 'https://hacker-news.firebaseio.com/v0',
            'enabled': True
        },
        'reddit': {
            'enabled': bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET),
            'subreddits': ['technology', 'programming', 'MachineLearning', 'IoT', 'arduino']
        },
        'youtube': {
            'enabled': bool(YOUTUBE_API_KEY),
            'max_results': 50
        },
        'discord': {
            'enabled': bool(DISCORD_BOT_TOKEN),
            'data_format': 'json'
        }
    }
    
    # Analysis settings
    ANALYSIS = {
        'default_timeframe_days': 30,
        'moving_average_window': 7,
        'top_contributors_limit': 10,
        'sample_posts_limit': 20
    }
    
    @classmethod
    def get_platform_config(cls, platform: str) -> Dict[str, Any]:
        """Get configuration for a specific platform"""
        return cls.PLATFORMS.get(platform, {})
    
    @classmethod
    def is_platform_enabled(cls, platform: str) -> bool:
        """Check if a platform is enabled and configured"""
        config = cls.get_platform_config(platform)
        return config.get('enabled', False)
    
    @classmethod
    def ensure_data_dir(cls) -> str:
        """Ensure data directory exists and return path"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        return cls.DATA_DIR

