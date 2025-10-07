"""
Real-time Data Collection Service
Collects hot posts for event-driven notifications
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..collectors import HackerNewsCollector, RedditCollector, YouTubeCollector
from ..config import Config

class RealtimeCollectionService:
    """Service for collecting real-time hot posts"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Data directories
        self.data_dir = Path(Config.DATA_DIR)
        self.realtime_dir = self.data_dir / 'realtime'
        self.realtime_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize collectors
        self.collectors = {
            'hackernews': HackerNewsCollector(),
            'reddit': RedditCollector(),
            'youtube': YouTubeCollector()
        }
        
        self.logger.info("RealtimeCollectionService initialized")
    
    def collect_hot_posts(self, limit_per_platform: int = 50) -> Dict[str, List[Dict]]:
        """
        Collect today's hot posts from all platforms
        
        Args:
            limit_per_platform: Maximum number of posts per platform
            
        Returns:
            Dictionary with hot posts from each platform
        """
        self.logger.info(f"Collecting hot posts (limit: {limit_per_platform} per platform)")
        
        hot_posts = {
            'hackernews': [],
            'reddit': [],
            'youtube': []
        }
        
        collection_time = datetime.now()
        
        # Collect from each platform
        for platform, collector in self.collectors.items():
            try:
                self.logger.info(f"Collecting hot posts from {platform}")
                posts = collector.get_recent_posts(limit=limit_per_platform)
                
                # Convert posts to dictionaries
                platform_posts = []
                for post in posts:
                    post_dict = self._post_to_dict(post)
                    post_dict['platform'] = platform
                    post_dict['collection_time'] = collection_time.isoformat()
                    platform_posts.append(post_dict)
                
                hot_posts[platform] = platform_posts
                self.logger.info(f"Collected {len(platform_posts)} posts from {platform}")
                
            except Exception as e:
                self.logger.error(f"Error collecting hot posts from {platform}: {e}")
                hot_posts[platform] = []
        
        # Save hot posts
        self._save_hot_posts(hot_posts, collection_time)
        
        return hot_posts
    
    def search_keywords_in_hot_posts(self, keywords: List[str], 
                                   hot_posts: Dict[str, List[Dict]] = None,
                                   exact_match: bool = True) -> List[Dict]:
        """
        Search for keywords in hot posts
        
        Args:
            keywords: List of keywords to search for
            hot_posts: Hot posts to search in (if None, collect new ones)
            exact_match: Whether to use exact phrase matching
            
        Returns:
            List of keyword mentions found
        """
        if hot_posts is None:
            hot_posts = self.collect_hot_posts()
        
        mentions = []
        
        for keyword in keywords:
            keyword_mentions = self._find_keyword_mentions(
                hot_posts, keyword, exact_match
            )
            mentions.extend(keyword_mentions)
        
        return mentions
    
    def _find_keyword_mentions(self, hot_posts: Dict[str, List[Dict]], 
                              keyword: str, exact_match: bool) -> List[Dict]:
        """Find keyword mentions in hot posts"""
        mentions = []
        
        for platform, posts in hot_posts.items():
            for post in posts:
                title = post.get('title', '')
                content = post.get('content', '')
                
                if self._contains_keyword(title + ' ' + content, keyword, exact_match):
                    mention = {
                        'keyword': keyword,
                        'platform': platform,
                        'post': post,
                        'found_at': datetime.now().isoformat()
                    }
                    mentions.append(mention)
        
        return mentions
    
    def _contains_keyword(self, text: str, keyword: str, exact_match: bool) -> bool:
        """Check if text contains keyword"""
        if not text or not keyword:
            return False
        
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        if exact_match:
            import re
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            return bool(re.search(pattern, text_lower))
        else:
            return keyword_lower in text_lower
    
    def _post_to_dict(self, post) -> Dict[str, Any]:
        """Convert post object to dictionary"""
        if hasattr(post, '__dict__'):
            return post.__dict__
        elif isinstance(post, dict):
            return post
        else:
            return {'content': str(post)}
    
    def _save_hot_posts(self, hot_posts: Dict[str, List[Dict]], collection_time: datetime):
        """Save hot posts to file"""
        filename = f"hot_posts_{collection_time.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.realtime_dir / filename
        
        data = {
            'collection_time': collection_time.isoformat(),
            'platforms': hot_posts,
            'total_posts': sum(len(posts) for posts in hot_posts.values())
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info(f"Hot posts saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving hot posts: {e}")
    
    def get_latest_hot_posts(self) -> Optional[Dict[str, List[Dict]]]:
        """Get the most recent hot posts"""
        hot_post_files = list(self.realtime_dir.glob('hot_posts_*.json'))
        
        if not hot_post_files:
            return None
        
        # Get the most recent file
        latest_file = max(hot_post_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r') as f:
                data = json.load(f)
                return data.get('platforms', {})
        except Exception as e:
            self.logger.error(f"Error loading latest hot posts: {e}")
            return None
    
    def cleanup_old_hot_posts(self, days_to_keep: int = 7):
        """Clean up old hot posts files"""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        
        for file_path in self.realtime_dir.glob('hot_posts_*.json'):
            try:
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_time:
                    file_path.unlink()
                    self.logger.info(f"Deleted old hot posts file: {file_path}")
            except Exception as e:
                self.logger.error(f"Error deleting {file_path}: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get real-time collection statistics"""
        hot_post_files = list(self.realtime_dir.glob('hot_posts_*.json'))
        
        stats = {
            'total_collections': len(hot_post_files),
            'latest_collection': None,
            'platforms': {}
        }
        
        if hot_post_files:
            # Get the most recent file
            latest_file = max(hot_post_files, key=lambda f: f.stat().st_mtime)
            stats['latest_collection'] = latest_file.name
            
            try:
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                    platforms = data.get('platforms', {})
                    
                    for platform, posts in platforms.items():
                        stats['platforms'][platform] = {
                            'posts_count': len(posts),
                            'latest_post_time': max(
                                (post.get('timestamp', '') for post in posts),
                                default=''
                            )
                        }
            except Exception as e:
                self.logger.error(f"Error reading latest collection stats: {e}")
        
        return stats
