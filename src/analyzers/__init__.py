"""
Platform-specific analyzers for BuzzScope
"""
from .base_analyzer import BaseAnalyzer
from .hackernews_analyzer import HackerNewsAnalyzer
from .reddit_analyzer import RedditAnalyzer
from .youtube_analyzer import YouTubeAnalyzer
from .discord_analyzer import DiscordAnalyzer

# Platform analyzer mapping
PLATFORM_ANALYZERS = {
    'hackernews': HackerNewsAnalyzer,
    'reddit': RedditAnalyzer,
    'youtube': YouTubeAnalyzer,
    'discord': DiscordAnalyzer,
}

__all__ = [
    'BaseAnalyzer',
    'HackerNewsAnalyzer',
    'RedditAnalyzer', 
    'YouTubeAnalyzer',
    'DiscordAnalyzer',
    'PLATFORM_ANALYZERS'
]

