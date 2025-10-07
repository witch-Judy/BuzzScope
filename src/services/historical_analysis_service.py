"""
Historical Analysis Service
Uses pre-collected historical data for volume and trend analysis
"""
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from ..collectors import RedditCollector, YouTubeCollector
from ..analyzers.historical_analyzer import HistoricalAnalyzer

class HistoricalAnalysisService:
    """Service for analyzing historical data"""
    
    def __init__(self):
        self.data_dir = "data"
        self.historical_analyzer = HistoricalAnalyzer()
        
        # Initialize real-time collectors for Reddit and YouTube
        self.reddit_collector = RedditCollector()
        self.youtube_collector = YouTubeCollector()
    
    def analyze_keyword(self, keyword: str, exact_match: bool = True) -> Dict[str, Any]:
        """
        Analyze keyword using historical data
        
        Args:
            keyword: Keyword to analyze
            exact_match: Whether to use exact phrase matching
            
        Returns:
            Analysis results for all platforms
        """
        print(f"🔍 Analyzing keyword: '{keyword}' (exact_match={exact_match})")
        
        results = {
            'keyword': keyword,
            'exact_match': exact_match,
            'analysis_time': datetime.now().isoformat(),
            'platforms': {}
        }
        
        # Analyze Hacker News (historical data)
        hn_result = self._analyze_hackernews_historical(keyword, exact_match)
        results['platforms']['hackernews'] = hn_result
        
        # Analyze Discord (historical data)
        discord_result = self._analyze_discord_historical(keyword, exact_match)
        results['platforms']['discord'] = discord_result
        
        # Analyze Reddit (real-time search with time=all)
        reddit_result = self._analyze_reddit_realtime(keyword, exact_match)
        results['platforms']['reddit'] = reddit_result
        
        # Analyze YouTube (real-time search)
        youtube_result = self._analyze_youtube_realtime(keyword, exact_match)
        results['platforms']['youtube'] = youtube_result
        
        return results
    
    def _analyze_hackernews_historical(self, keyword: str, exact_match: bool) -> Dict[str, Any]:
        """Analyze Hacker News using historical data"""
        print(f"  📱 Analyzing Hacker News (historical)...")
        
        try:
            # Check if historical data exists
            hn_data_dir = os.path.join(self.data_dir, "hackernews")
            if not os.path.exists(hn_data_dir):
                return {'error': 'No Hacker News historical data found'}
            
            # Look for keyword-specific files
            keyword_files = []
            for file in os.listdir(hn_data_dir):
                if keyword.lower().replace(' ', '_') in file.lower():
                    keyword_files.append(os.path.join(hn_data_dir, file))
            
            if not keyword_files:
                return {'error': f'No historical data found for keyword: {keyword}'}
            
            # Load and analyze data
            all_posts = []
            for file_path in keyword_files:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    posts = data.get('posts', [])
                    all_posts.extend(posts)
            
            # Apply exact match filtering if needed
            if exact_match:
                filtered_posts = self._filter_exact_match(all_posts, keyword)
            else:
                filtered_posts = all_posts
            
            return {
                'status': 'success',
                'total_posts': len(filtered_posts),
                'data_source': 'cache',
                'files_used': len(keyword_files),
                'date_range': self._get_date_range(filtered_posts)
            }
            
        except Exception as e:
            return {'error': f'Hacker News analysis failed: {str(e)}'}
    
    def _analyze_discord_historical(self, keyword: str, exact_match: bool) -> Dict[str, Any]:
        """Analyze Discord using historical data"""
        print(f"  📱 Analyzing Discord (historical)...")
        
        try:
            # Check if historical data exists
            discord_data_dir = os.path.join(self.data_dir, "discord")
            if not os.path.exists(discord_data_dir):
                return {'error': 'No Discord historical data found'}
            
            # Search through all community directories
            all_posts = []
            communities = ['industry40', 'soliscada', 'supos']
            
            for community in communities:
                community_dir = os.path.join(discord_data_dir, community)
                if os.path.exists(community_dir):
                    posts = self._search_discord_community(community_dir, keyword, exact_match)
                    all_posts.extend(posts)
            
            return {
                'status': 'success',
                'total_posts': len(all_posts),
                'data_source': 'cache',
                'communities_searched': len(communities),
                'date_range': self._get_date_range(all_posts)
            }
            
        except Exception as e:
            return {'error': f'Discord analysis failed: {str(e)}'}
    
    def _analyze_reddit_realtime(self, keyword: str, exact_match: bool) -> Dict[str, Any]:
        """Analyze Reddit using real-time search with time=all"""
        print(f"  📱 Analyzing Reddit (real-time, time=all)...")
        
        try:
            # Use Reddit search API with time=all
            posts = self.reddit_collector.search_keyword(
                keyword=keyword,
                days_back=365*5,  # 5 years
                exact_match=exact_match,
                use_global=True
            )
            
            # Limit to top 100 most relevant posts
            posts = posts[:100]
            
            return {
                'status': 'success',
                'total_posts': len(posts),
                'data_source': 'real-time',
                'search_method': 'time=all',
                'date_range': self._get_date_range(posts)
            }
            
        except Exception as e:
            return {'error': f'Reddit analysis failed: {str(e)}'}
    
    def _analyze_youtube_realtime(self, keyword: str, exact_match: bool) -> Dict[str, Any]:
        """Analyze YouTube using real-time search"""
        print(f"  📱 Analyzing YouTube (real-time)...")
        
        try:
            # Use YouTube search API
            posts = self.youtube_collector.search_keyword(
                keyword=keyword,
                days_back=365*5,  # 5 years
                exact_match=exact_match
            )
            
            # Limit to top 100 most relevant videos
            posts = posts[:100]
            
            return {
                'status': 'success',
                'total_posts': len(posts),
                'data_source': 'real-time',
                'search_method': 'keyword_search',
                'date_range': self._get_date_range(posts)
            }
            
        except Exception as e:
            return {'error': f'YouTube analysis failed: {str(e)}'}
    
    def _search_discord_community(self, community_dir: str, keyword: str, exact_match: bool) -> List[Dict]:
        """Search Discord community directory for keyword mentions"""
        posts = []
        
        for file in os.listdir(community_dir):
            if file.endswith(('.json', '.csv')):
                file_path = os.path.join(community_dir, file)
                try:
                    if file.endswith('.json'):
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                messages = data
                            else:
                                messages = data.get('messages', [])
                            
                            for message in messages:
                                content = message.get('content', '')
                                if self._contains_keyword(content, keyword, exact_match):
                                    posts.append({
                                        'content': content,
                                        'author': message.get('author', {}).get('name', 'Unknown'),
                                        'timestamp': message.get('timestamp', ''),
                                        'community': os.path.basename(community_dir)
                                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue
        
        return posts
    
    def _contains_keyword(self, text: str, keyword: str, exact_match: bool) -> bool:
        """Check if text contains keyword"""
        if not text or not keyword:
            return False
        
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        if exact_match:
            return keyword_lower in text_lower
        else:
            # For exact phrase matching, use word boundaries
            import re
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            return bool(re.search(pattern, text_lower))
    
    def _filter_exact_match(self, posts: List[Dict], keyword: str) -> List[Dict]:
        """Filter posts for exact keyword matches"""
        filtered = []
        for post in posts:
            title = post.get('title', '')
            content = post.get('content', '')
            if self._contains_keyword(title + ' ' + content, keyword, True):
                filtered.append(post)
        return filtered
    
    def _get_date_range(self, posts: List[Dict]) -> Dict[str, str]:
        """Get date range from posts"""
        if not posts:
            return {'start': None, 'end': None}
        
        timestamps = []
        for post in posts:
            timestamp = post.get('timestamp', '')
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        # Parse various timestamp formats
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    else:
                        dt = timestamp
                    timestamps.append(dt)
                except:
                    continue
        
        if timestamps:
            timestamps.sort()
            return {
                'start': timestamps[0].isoformat(),
                'end': timestamps[-1].isoformat()
            }
        
        return {'start': None, 'end': None}
