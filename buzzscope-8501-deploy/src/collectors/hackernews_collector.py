"""
Hacker News data collector
"""
import requests
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .base_collector import BaseCollector
from ..models import HackerNewsPost
from ..config import Config

class HackerNewsCollector(BaseCollector):
    """Collector for Hacker News data"""
    
    def __init__(self):
        super().__init__("hackernews")
        self.api_url = Config.get_platform_config('hackernews')['api_url']
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BuzzScope/1.0 (Keyword Tracking Tool)'
        })
    
    def search_keyword(self, keyword: str, days_back: int = 90, exact_match: bool = False) -> List[HackerNewsPost]:
        """Search Hacker News for keyword mentions"""
        self.logger.info(f"Searching Hacker News for keyword: {keyword} (exact_match={exact_match})")
        
        # Get recent stories and comments
        all_posts = []
        
        # Get more stories to increase chances of finding keyword matches
        # Hacker News API doesn't support time-based search, so we get more recent stories
        
        # Get top stories (increase limit for better coverage)
        stories = self._get_top_stories(limit=500)
        all_posts.extend(stories)
        
        # Get new stories (increase limit for better coverage)
        new_stories = self._get_new_stories(limit=500)
        all_posts.extend(new_stories)
        
        # Get best stories (additional data source)
        best_stories = self._get_best_stories(limit=200)
        all_posts.extend(best_stories)
        
        # Get Show HN and Ask HN posts
        show_hn_posts = self._get_show_hn_posts(limit=100)
        all_posts.extend(show_hn_posts)
        
        ask_hn_posts = self._get_ask_hn_posts(limit=100)
        all_posts.extend(ask_hn_posts)
        
        # Remove duplicates based on post_id
        seen_ids = set()
        unique_posts = []
        for post in all_posts:
            if post.post_id not in seen_ids:
                seen_ids.add(post.post_id)
                unique_posts.append(post)
        
        self.logger.info(f"Collected {len(unique_posts)} unique stories from Hacker News")
        
        # Filter by keyword and date
        keyword_posts = self.extract_keyword_mentions(unique_posts, keyword, exact_match)
        filtered_posts = self.filter_by_date_range(keyword_posts, days_back)
        
        self.logger.info(f"Found {len(filtered_posts)} posts mentioning '{keyword}' (exact_match={exact_match})")
        
        # 如果没有找到精确匹配的结果，尝试子字符串匹配
        if len(filtered_posts) == 0 and exact_match:
            self.logger.info(f"No exact matches found for '{keyword}', trying substring matching...")
            keyword_posts_substring = self.extract_keyword_mentions(unique_posts, keyword, exact_match=False)
            filtered_posts = self.filter_by_date_range(keyword_posts_substring, days_back)
            self.logger.info(f"Found {len(filtered_posts)} posts with substring matching")
        
        return self.clean_posts(filtered_posts)
    
    def get_recent_posts(self, limit: int = 100) -> List[HackerNewsPost]:
        """Get recent posts from Hacker News"""
        self.logger.info(f"Getting {limit} recent posts from Hacker News")
        
        posts = []
        
        # Get top stories
        top_stories = self._get_top_stories(limit // 2)
        posts.extend(top_stories)
        
        # Get new stories
        new_stories = self._get_new_stories(limit // 2)
        posts.extend(new_stories)
        
        # Remove duplicates and limit
        unique_posts = self._remove_duplicates(posts)
        return unique_posts[:limit]
    
    def _get_top_stories(self, limit: int = 50) -> List[HackerNewsPost]:
        """Get top stories from Hacker News (all content types)"""
        try:
            response = self.session.get(f"{self.api_url}/topstories.json")
            response.raise_for_status()
            story_ids = response.json()[:limit]
            
            posts = []
            for story_id in story_ids:
                post = self._get_item(story_id)
                if post:  # 收集所有类型，不只是story
                    posts.append(post)
                time.sleep(0.1)  # Rate limiting
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error getting top stories: {e}")
            return []
    
    def _get_new_stories(self, limit: int = 50) -> List[HackerNewsPost]:
        """Get new stories from Hacker News (all content types)"""
        try:
            response = self.session.get(f"{self.api_url}/newstories.json")
            response.raise_for_status()
            story_ids = response.json()[:limit]
            
            posts = []
            for story_id in story_ids:
                post = self._get_item(story_id)
                if post:  # 收集所有类型，不只是story
                    posts.append(post)
                time.sleep(0.1)  # Rate limiting
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error getting new stories: {e}")
            return []
    
    def _get_best_stories(self, limit: int = 50) -> List[HackerNewsPost]:
        """Get best stories from Hacker News (all content types)"""
        try:
            response = self.session.get(f"{self.api_url}/beststories.json")
            response.raise_for_status()
            story_ids = response.json()[:limit]
            
            posts = []
            for story_id in story_ids:
                post = self._get_item(story_id)
                if post:  # 收集所有类型，不只是story
                    posts.append(post)
                time.sleep(0.1)  # Rate limiting
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error getting best stories: {e}")
            return []
    
    def _get_show_hn_posts(self, limit: int = 30) -> List[HackerNewsPost]:
        """Get Show HN posts from Hacker News"""
        try:
            response = self.session.get(f"{self.api_url}/showstories.json")
            response.raise_for_status()
            story_ids = response.json()[:limit]
            
            posts = []
            for story_id in story_ids:
                post = self._get_item(story_id)
                if post:
                    posts.append(post)
                time.sleep(0.1)  # Rate limiting
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error getting Show HN posts: {e}")
            return []
    
    def _get_ask_hn_posts(self, limit: int = 30) -> List[HackerNewsPost]:
        """Get Ask HN posts from Hacker News"""
        try:
            response = self.session.get(f"{self.api_url}/askstories.json")
            response.raise_for_status()
            story_ids = response.json()[:limit]
            
            posts = []
            for story_id in story_ids:
                post = self._get_item(story_id)
                if post:
                    posts.append(post)
                time.sleep(0.1)  # Rate limiting
            
            return posts
            
        except Exception as e:
            self.logger.error(f"Error getting Ask HN posts: {e}")
            return []
    
    def _get_item(self, item_id: int) -> HackerNewsPost:
        """Get a specific item from Hacker News"""
        try:
            response = self.session.get(f"{self.api_url}/item/{item_id}.json")
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return None
            
            # Convert timestamp
            timestamp = datetime.fromtimestamp(data.get('time', 0))
            
            # Extract URL
            url = data.get('url', '')
            if not url and data.get('type') == 'story':
                url = f"https://news.ycombinator.com/item?id={item_id}"
            
            return HackerNewsPost(
                platform="hackernews",
                post_id=str(item_id),
                title=data.get('title', ''),
                content=data.get('text', ''),
                author=data.get('by', ''),
                timestamp=timestamp,
                url=url,
                score=data.get('score', 0),
                descendants=data.get('descendants', 0),
                type=data.get('type', 'story'),
                metadata={
                    'kids': data.get('kids', []),
                    'parent': data.get('parent'),
                    'deleted': data.get('deleted', False),
                    'dead': data.get('dead', False)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error getting item {item_id}: {e}")
            return None
    
    def _remove_duplicates(self, posts: List[HackerNewsPost]) -> List[HackerNewsPost]:
        """Remove duplicate posts based on post_id"""
        seen_ids = set()
        unique_posts = []
        
        for post in posts:
            if post.post_id not in seen_ids:
                seen_ids.add(post.post_id)
                unique_posts.append(post)
        
        return unique_posts

