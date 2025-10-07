"""
Data models and schemas for BuzzScope
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
import pandas as pd

@dataclass
class BasePost:
    """Base class for all platform posts"""
    platform: str
    post_id: str
    title: str
    content: str
    author: str
    timestamp: datetime
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create instance from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class HackerNewsPost(BasePost):
    """Hacker News specific post data"""
    score: int = 0
    descendants: int = 0  # comment count
    type: str = "story"  # story, comment, poll, etc.
    
    def __post_init__(self):
        self.platform = "hackernews"

@dataclass
class RedditPost(BasePost):
    """Reddit specific post data"""
    subreddit: str = ""
    score: int = 0
    num_comments: int = 0
    upvote_ratio: float = 0.0
    is_self: bool = True
    
    def __post_init__(self):
        self.platform = "reddit"

@dataclass
class YouTubePost(BasePost):
    """YouTube specific post data"""
    video_id: str = ""
    channel_id: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    duration: Optional[str] = None
    
    def __post_init__(self):
        self.platform = "youtube"

@dataclass
class DiscordPost(BasePost):
    """Discord specific post data"""
    channel_id: str = ""
    guild_id: str = ""
    message_type: str = "default"
    reactions: Optional[Dict[str, int]] = None
    
    def __post_init__(self):
        self.platform = "discord"

# Analysis result models
@dataclass
class KeywordMetrics:
    """Metrics for a keyword across platforms"""
    keyword: str
    platform: str
    total_mentions: int
    unique_authors: int
    total_interactions: int  # likes, upvotes, comments, views
    date_range: tuple  # (start_date, end_date)
    daily_metrics: Optional[pd.DataFrame] = None
    top_contributors: Optional[List[Dict[str, Any]]] = None
    sample_posts: Optional[List[Dict[str, Any]]] = None
    insights: Optional[List[str]] = None

@dataclass
class ComparisonMetrics:
    """Comparison metrics between multiple keywords"""
    keywords: List[str]
    platform: str
    comparison_data: pd.DataFrame
    date_range: tuple
    insights: Optional[List[str]] = None

# Platform registry for dynamic loading
PLATFORM_MODELS = {
    'hackernews': HackerNewsPost,
    'reddit': RedditPost,
    'youtube': YouTubePost,
    'discord': DiscordPost
}

def get_post_model(platform: str) -> type:
    """Get the appropriate post model for a platform"""
    return PLATFORM_MODELS.get(platform, BasePost)

