"""
Data Collection Service V2
Handles both historical and real-time data collection with caching
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from ..collectors import HackerNewsCollector, RedditCollector, YouTubeCollector, DiscordIncrementalCollector
from ..config import Config

class DataCollectionServiceV2:
    """Enhanced data collection service with caching and historical data support"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Data directories
        self.data_dir = Path(Config.DATA_DIR)
        self.historical_dir = self.data_dir / 'historical'
        self.cache_dir = self.data_dir / 'cache'
        
        # Ensure directories exist
        for platform in ['hackernews', 'reddit', 'youtube', 'discord']:
            (self.historical_dir / platform).mkdir(parents=True, exist_ok=True)
            (self.cache_dir / platform).mkdir(parents=True, exist_ok=True)
        
        # Initialize collectors
        self.collectors = {
            'hackernews': HackerNewsCollector(),
            'reddit': RedditCollector(),
            'youtube': YouTubeCollector(),
            'discord': DiscordIncrementalCollector()
        }
        
        self.logger.info("DataCollectionServiceV2 initialized")
    
    def collect_keyword_data(self, keyword: str, exact_match: bool = True, 
                           force_refresh: bool = False) -> Dict[str, Any]:
        """
        Collect data for a keyword across all platforms
        
        Args:
            keyword: Keyword to collect data for
            exact_match: Whether to use exact phrase matching
            force_refresh: Force refresh even if cached data exists
            
        Returns:
            Dictionary with collection results for each platform
        """
        self.logger.info(f"Collecting data for keyword: '{keyword}' (exact_match={exact_match})")
        
        results = {
            'keyword': keyword,
            'exact_match': exact_match,
            'collection_time': datetime.now().isoformat(),
            'platforms': {}
        }
        
        # Collect from each platform
        for platform in ['hackernews', 'reddit', 'youtube', 'discord']:
            try:
                platform_result = self._collect_platform_data(
                    platform, keyword, exact_match, force_refresh
                )
                results['platforms'][platform] = platform_result
            except Exception as e:
                self.logger.error(f"Error collecting {platform} data: {e}")
                results['platforms'][platform] = {
                    'status': 'error',
                    'error': str(e),
                    'posts': []
                }
        
        # Save collection summary
        self._save_collection_summary(results)
        
        return results
    
    def _collect_platform_data(self, platform: str, keyword: str, 
                              exact_match: bool, force_refresh: bool) -> Dict[str, Any]:
        """Collect data for a specific platform"""
        self.logger.info(f"Collecting {platform} data for '{keyword}'")
        
        # Check if cached data exists
        cache_file = self.cache_dir / platform / f"{self._sanitize_keyword(keyword)}.json"
        
        if not force_refresh and cache_file.exists():
            self.logger.info(f"Using cached data for {platform}")
            return self._load_cached_data(cache_file)
        
        # Collect new data based on platform strategy
        if platform in ['hackernews', 'discord']:
            # Use historical data for HN and Discord
            posts = self._collect_historical_data(platform, keyword, exact_match)
        else:
            # Use time=all strategy for Reddit and YouTube
            posts = self._collect_time_all_data(platform, keyword, exact_match)
        
        # Save to cache
        result = {
            'status': 'success',
            'data_source': 'cache' if platform in ['hackernews', 'discord'] else 'time_all',
            'total_posts': len(posts),
            'posts': [self._post_to_dict(post) for post in posts],
            'collection_time': datetime.now().isoformat(),
            'keyword': keyword,
            'exact_match': exact_match
        }
        
        self._save_cached_data(cache_file, result)
        
        return result
    
    def _collect_historical_data(self, platform: str, keyword: str, exact_match: bool) -> List:
        """Collect data from historical sources (HN, Discord)"""
        self.logger.info(f"Collecting historical data from {platform}")
        
        if platform == 'hackernews':
            return self._collect_hackernews_historical(keyword, exact_match)
        elif platform == 'discord':
            return self._collect_discord_historical(keyword, exact_match)
        else:
            return []
    
    def _collect_time_all_data(self, platform: str, keyword: str, exact_match: bool) -> List:
        """Collect data using time=all strategy (Reddit, YouTube)"""
        self.logger.info(f"Collecting time=all data from {platform}")
        
        collector = self.collectors[platform]
        
        if platform == 'reddit':
            # Reddit: search with time=all (5 years)
            posts = collector.search_keyword(
                keyword=keyword,
                days_back=365*5,  # 5 years
                exact_match=exact_match,
                use_global=True
            )
            # Limit to top 100 most relevant
            return posts[:100]
            
        elif platform == 'youtube':
            # YouTube: search with time=all (5 years)
            posts = collector.search_keyword(
                keyword=keyword,
                days_back=365*5,  # 5 years
                exact_match=exact_match
            )
            # Limit to top 100 most relevant
            return posts[:100]
        
        return []
    
    def _collect_hackernews_historical(self, keyword: str, exact_match: bool) -> List:
        """Collect Hacker News data from historical files"""
        hn_dir = self.historical_dir / 'hackernews'
        posts = []
        
        if not hn_dir.exists():
            self.logger.warning("No Hacker News historical data directory found")
            return posts
        
        # Search through all JSON files
        for file_path in hn_dir.glob('*.json'):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    file_posts = data.get('posts', [])
                    
                    # Filter by keyword
                    filtered_posts = self._filter_posts_by_keyword(file_posts, keyword, exact_match)
                    posts.extend(filtered_posts)
                    
            except Exception as e:
                self.logger.warning(f"Error reading {file_path}: {e}")
                continue
        
        self.logger.info(f"Found {len(posts)} Hacker News posts for '{keyword}'")
        return posts
    
    def _collect_discord_historical(self, keyword: str, exact_match: bool) -> List:
        """Collect Discord data from historical files"""
        discord_dir = self.data_dir / 'discord'
        posts = []
        
        if not discord_dir.exists():
            self.logger.warning("No Discord historical data directory found")
            return posts
        
        # Search through all community directories
        for community_dir in discord_dir.iterdir():
            if community_dir.is_dir():
                community_posts = self._search_discord_community(
                    community_dir, keyword, exact_match
                )
                posts.extend(community_posts)
        
        self.logger.info(f"Found {len(posts)} Discord posts for '{keyword}'")
        return posts
    
    def _search_discord_community(self, community_dir: Path, keyword: str, exact_match: bool) -> List:
        """Search Discord community directory for keyword mentions"""
        posts = []
        
        for file_path in community_dir.glob('*.csv'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # Skip header
                    for line in lines[1:]:
                        parts = line.strip().split(',')
                        if len(parts) >= 4:
                            content = parts[3]  # Content is usually in 4th column
                            
                            if self._contains_keyword(content, keyword, exact_match):
                                post = {
                                    'content': content,
                                    'author': parts[1] if len(parts) > 1 else 'Unknown',
                                    'timestamp': parts[0] if len(parts) > 0 else '',
                                    'community': community_dir.name,
                                    'platform': 'discord'
                                }
                                posts.append(post)
                                
            except Exception as e:
                self.logger.warning(f"Error reading {file_path}: {e}")
                continue
        
        return posts
    
    def _filter_posts_by_keyword(self, posts: List[Dict], keyword: str, exact_match: bool) -> List[Dict]:
        """Filter posts by keyword"""
        filtered = []
        keyword_lower = keyword.lower()
        
        for post in posts:
            title = post.get('title', '')
            content = post.get('content', '')
            
            if self._contains_keyword(title + ' ' + content, keyword_lower, exact_match):
                filtered.append(post)
        
        return filtered
    
    def _contains_keyword(self, text: str, keyword: str, exact_match: bool) -> bool:
        """Check if text contains keyword"""
        if not text or not keyword:
            return False
        
        text_lower = text.lower()
        
        if exact_match:
            import re
            pattern = r'\b' + re.escape(keyword) + r'\b'
            return bool(re.search(pattern, text_lower))
        else:
            return keyword in text_lower
    
    def _sanitize_keyword(self, keyword: str) -> str:
        """Sanitize keyword for filename"""
        import re
        # Replace spaces and special characters with underscores
        sanitized = re.sub(r'[^\w\-_]', '_', keyword.lower())
        return sanitized
    
    def _post_to_dict(self, post) -> Dict[str, Any]:
        """Convert post object to dictionary"""
        if hasattr(post, '__dict__'):
            return post.__dict__
        elif isinstance(post, dict):
            return post
        else:
            return {'content': str(post)}
    
    def _load_cached_data(self, cache_file: Path) -> Dict[str, Any]:
        """Load cached data from file"""
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                data['status'] = 'cached'
                return data
        except Exception as e:
            self.logger.error(f"Error loading cached data from {cache_file}: {e}")
            return {'status': 'error', 'error': str(e), 'posts': []}
    
    def _save_cached_data(self, cache_file: Path, data: Dict[str, Any]):
        """Save data to cache file"""
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info(f"Cached data saved to {cache_file}")
        except Exception as e:
            self.logger.error(f"Error saving cached data to {cache_file}: {e}")
    
    def _save_collection_summary(self, results: Dict[str, Any]):
        """Save collection summary"""
        summary_file = self.cache_dir / f"collection_summary_{self._sanitize_keyword(results['keyword'])}.json"
        
        try:
            with open(summary_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            self.logger.info(f"Collection summary saved to {summary_file}")
        except Exception as e:
            self.logger.error(f"Error saving collection summary: {e}")
    
    def get_cached_keywords(self) -> List[str]:
        """Get list of keywords with cached data"""
        keywords = set()
        
        for platform_dir in self.cache_dir.iterdir():
            if platform_dir.is_dir():
                for cache_file in platform_dir.glob('*.json'):
                    # Extract keyword from filename
                    keyword = cache_file.stem
                    keywords.add(keyword)
        
        return sorted(list(keywords))
    
    def clear_cache(self, keyword: str = None):
        """Clear cache for specific keyword or all keywords"""
        if keyword:
            sanitized = self._sanitize_keyword(keyword)
            for platform_dir in self.cache_dir.iterdir():
                if platform_dir.is_dir():
                    cache_file = platform_dir / f"{sanitized}.json"
                    if cache_file.exists():
                        cache_file.unlink()
                        self.logger.info(f"Cleared cache for '{keyword}' in {platform_dir.name}")
        else:
            # Clear all cache
            for platform_dir in self.cache_dir.iterdir():
                if platform_dir.is_dir():
                    for cache_file in platform_dir.glob('*.json'):
                        cache_file.unlink()
            self.logger.info("Cleared all cache")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        stats = {
            'total_cached_keywords': len(self.get_cached_keywords()),
            'platforms': {}
        }
        
        for platform in ['hackernews', 'reddit', 'youtube', 'discord']:
            platform_dir = self.cache_dir / platform
            if platform_dir.exists():
                cache_files = list(platform_dir.glob('*.json'))
                stats['platforms'][platform] = {
                    'cached_keywords': len(cache_files),
                    'cache_files': [f.name for f in cache_files]
                }
            else:
                stats['platforms'][platform] = {
                    'cached_keywords': 0,
                    'cache_files': []
                }
        
        return stats
