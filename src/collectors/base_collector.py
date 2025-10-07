"""
Base collector class for all platform data collectors
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from ..models import BasePost

logger = logging.getLogger(__name__)

class BaseCollector(ABC):
    """Abstract base class for all data collectors"""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.logger = logging.getLogger(f"{__name__}.{platform}")
    
    @abstractmethod
    def search_keyword(self, keyword: str, days_back: int = 30, exact_match: bool = False) -> List[BasePost]:
        """
        Search for posts containing the keyword
        
        Args:
            keyword: The keyword to search for
            days_back: Number of days to look back
            exact_match: If True, use exact phrase matching. If False, use substring matching.
            
        Returns:
            List of posts containing the keyword
        """
        pass
    
    @abstractmethod
    def get_recent_posts(self, limit: int = 100) -> List[BasePost]:
        """
        Get recent posts from the platform
        
        Args:
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of recent posts
        """
        pass
    
    def filter_by_date_range(self, posts: List[BasePost], days_back: int) -> List[BasePost]:
        """Filter posts by date range"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        return [post for post in posts if post.timestamp >= cutoff_date]
    
    def extract_keyword_mentions(self, posts: List[BasePost], keyword: str, 
                                exact_match: bool = False) -> List[BasePost]:
        """
        Extract posts that mention the keyword
        
        Args:
            posts: List of posts to search
            keyword: Keyword to search for
            exact_match: If True, use exact phrase matching. If False, use substring matching.
        """
        keyword_lower = keyword.lower()
        mentions = []
        
        for post in posts:
            title_lower = post.title.lower()
            content_lower = post.content.lower()
            
            if exact_match:
                # Exact phrase matching - keyword must appear as complete phrase
                if (self._exact_phrase_match(title_lower, keyword_lower) or 
                    self._exact_phrase_match(content_lower, keyword_lower)):
                    mentions.append(post)
            else:
                # Substring matching - keyword can be part of a word
                if (keyword_lower in title_lower or keyword_lower in content_lower):
                    mentions.append(post)
        
        return mentions
    
    def _exact_phrase_match(self, text: str, phrase: str) -> bool:
        """
        Check if phrase appears as exact phrase in text (not as part of another word)
        
        Args:
            text: Text to search in
            phrase: Phrase to search for
            
        Returns:
            True if phrase appears as complete phrase
        """
        import re
        
        # Create regex pattern that matches the phrase as whole words
        # Handle special characters in the phrase
        escaped_phrase = re.escape(phrase)
        pattern = r'\b' + escaped_phrase + r'\b'
        
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def validate_post(self, post: BasePost) -> bool:
        """Validate that a post has required fields"""
        required_fields = ['post_id', 'title', 'content', 'author', 'timestamp']
        return all(getattr(post, field, None) is not None for field in required_fields)
    
    def clean_posts(self, posts: List[BasePost]) -> List[BasePost]:
        """Clean and validate posts"""
        cleaned = []
        for post in posts:
            if self.validate_post(post):
                # Basic content cleaning
                post.content = self._clean_text(post.content)
                post.title = self._clean_text(post.title)
                cleaned.append(post)
            else:
                self.logger.warning(f"Invalid post skipped: {getattr(post, 'post_id', 'unknown')}")
        
        return cleaned
    
    def _clean_text(self, text: str) -> str:
        """Basic text cleaning"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove HTML tags (basic)
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        return text.strip()
    
    def get_collection_stats(self, posts: List[BasePost]) -> Dict[str, Any]:
        """Get statistics about collected posts"""
        if not posts:
            return {
                'total_posts': 0,
                'date_range': None,
                'unique_authors': 0,
                'platform': self.platform
            }
        
        timestamps = [post.timestamp for post in posts]
        authors = [post.author for post in posts]
        
        return {
            'total_posts': len(posts),
            'date_range': (min(timestamps), max(timestamps)),
            'unique_authors': len(set(authors)),
            'platform': self.platform
        }

