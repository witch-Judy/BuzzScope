"""
Data collectors for different platforms
"""
from .base_collector import BaseCollector
from .hackernews_collector import HackerNewsCollector

# Optional imports - only import if dependencies are available
try:
    from .reddit_collector import RedditCollector
except ImportError:
    RedditCollector = None

try:
    from .youtube_collector import YouTubeCollector
except ImportError:
    YouTubeCollector = None

try:
    from .discord_collector import DiscordCollector
except ImportError:
    DiscordCollector = None

try:
    from .discord_incremental_collector import DiscordIncrementalCollector
except ImportError:
    DiscordIncrementalCollector = None

__all__ = [
    'BaseCollector',
    'HackerNewsCollector', 
    'RedditCollector',
    'YouTubeCollector',
    'DiscordCollector',
    'DiscordIncrementalCollector'
]

