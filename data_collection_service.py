#!/usr/bin/env python3
"""
Data Collection Service for BuzzScope
Unified service for collecting and caching keyword data across all platforms
"""
import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.collectors.historical_collector import HistoricalCollector
from src.collectors import HackerNewsCollector, RedditCollector, YouTubeCollector, DiscordCollector
from src.collectors.discord_incremental_collector import DiscordIncrementalCollector
from src.storage import BuzzScopeStorage
from src.config import Config

class DataCollectionService:
    """Unified data collection service for keywords"""
    
    def __init__(self):
        self.data_dir = './data'
        self.historical_dir = os.path.join(self.data_dir, 'cache')  # 更新为cache目录
        self.processed_dir = os.path.join(self.data_dir, 'processed')
        self.raw_dir = os.path.join(self.data_dir, 'raw')
        
        # Ensure directories exist
        for platform in ['hackernews', 'reddit', 'youtube', 'discord']:
            os.makedirs(os.path.join(self.historical_dir, platform), exist_ok=True)
            os.makedirs(os.path.join(self.processed_dir, platform), exist_ok=True)
            os.makedirs(os.path.join(self.raw_dir, platform), exist_ok=True)
        
        # Initialize collectors
        self.collectors = {
            'hackernews': HackerNewsCollector(),
            'reddit': RedditCollector(),
            'youtube': YouTubeCollector(),
            'discord': DiscordIncrementalCollector()  # Use incremental collector for Discord
        }
        
        self.storage = BuzzScopeStorage()
        self.historical_collector = HistoricalCollector()
    
    def collect_keyword_data(self, keyword: str, days_back: int = 30, 
                           platforms: List[str] = None, exact_match: bool = False,
                           use_historical: bool = True) -> Dict[str, Any]:
        """
        Collect comprehensive data for a keyword across all platforms
        
        Args:
            keyword: Keyword to collect data for
            days_back: Number of days to look back
            platforms: List of platforms to collect from (None = all)
            exact_match: Whether to use exact phrase matching
            use_historical: Whether to use historical collection methods
            
        Returns:
            Collection results and statistics
        """
        if platforms is None:
            platforms = ['hackernews', 'reddit', 'youtube', 'discord']
        
        print(f"🚀 Collecting data for keyword: '{keyword}'")
        print(f"📅 Time range: {days_back} days back")
        print(f"📱 Platforms: {', '.join(platforms)}")
        print(f"🎯 Exact match: {exact_match}")
        print(f"📚 Use historical: {use_historical}")
        print("=" * 60)
        
        results = {
            'keyword': keyword,
            'collection_time': datetime.now().isoformat(),
            'days_back': days_back,
            'exact_match': exact_match,
            'platforms': {},
            'summary': {
                'total_posts': 0,
                'total_platforms': 0,
                'successful_platforms': 0,
                'failed_platforms': 0
            }
        }
        
        # Check if we already have historical data
        if use_historical:
            historical_data = self._check_historical_data(keyword)
            if historical_data:
                print(f"📚 Found existing historical data for '{keyword}'")
                return self._load_historical_data(keyword, platforms)
        
        # Collect from each platform
        for platform in platforms:
            if platform not in self.collectors:
                print(f"❌ Unknown platform: {platform}")
                continue
            
            print(f"\n📱 Collecting from {platform.upper()}...")
            
            try:
                collector = self.collectors[platform]
                
                # Use platform-specific collection methods
                if platform == 'hackernews':
                    posts = self._collect_hackernews_data(collector, keyword, days_back, exact_match)
                elif platform == 'reddit':
                    posts = self._collect_reddit_data(collector, keyword, days_back, exact_match)
                elif platform == 'youtube':
                    posts = self._collect_youtube_data(collector, keyword, days_back, exact_match)
                elif platform == 'discord':
                    posts = self._collect_discord_data(collector, keyword, days_back, exact_match)
                else:
                    posts = []
                
                if posts:
                    # Save to processed storage
                    self.storage.save_posts(posts, platform)
                    
                    # Save to historical cache
                    self._save_historical_cache(keyword, platform, posts, days_back)
                    
                    results['platforms'][platform] = {
                        'status': 'success',
                        'posts_collected': len(posts),
                        'date_range': self._get_date_range(posts),
                        'sample_posts': self._get_sample_posts(posts, 3)
                    }
                    
                    results['summary']['total_posts'] += len(posts)
                    results['summary']['successful_platforms'] += 1
                    
                    print(f"✅ {platform}: {len(posts)} posts collected")
                else:
                    results['platforms'][platform] = {
                        'status': 'no_data',
                        'posts_collected': 0,
                        'message': 'No posts found for this keyword'
                    }
                    results['summary']['failed_platforms'] += 1
                    print(f"⚠️  {platform}: No posts found")
                
            except Exception as e:
                results['platforms'][platform] = {
                    'status': 'error',
                    'posts_collected': 0,
                    'error': str(e)
                }
                results['summary']['failed_platforms'] += 1
                print(f"❌ {platform}: Error - {e}")
        
        results['summary']['total_platforms'] = len(platforms)
        
        # Save collection summary
        self._save_collection_summary(keyword, results)
        
        print(f"\n✅ Collection complete!")
        print(f"📊 Total posts: {results['summary']['total_posts']}")
        print(f"✅ Successful platforms: {results['summary']['successful_platforms']}")
        print(f"❌ Failed platforms: {results['summary']['failed_platforms']}")
        
        return results
    
    def _collect_hackernews_data(self, collector, keyword: str, days_back: int, exact_match: bool) -> List:
        """Collect Hacker News data with comprehensive coverage"""
        print("  🔥 Collecting from Hacker News (comprehensive)...")
        
        # Collect from multiple sources
        all_posts = []
        
        # Get top stories
        top_posts = collector.search_keyword(keyword, days_back, exact_match)
        all_posts.extend(top_posts)
        
        # Get Show HN posts
        try:
            show_posts = collector._get_show_hn_posts(limit=50)
            show_filtered = collector.extract_keyword_mentions(show_posts, keyword, exact_match)
            all_posts.extend(show_filtered)
        except:
            pass
        
        # Get Ask HN posts
        try:
            ask_posts = collector._get_ask_hn_posts(limit=50)
            ask_filtered = collector.extract_keyword_mentions(ask_posts, keyword, exact_match)
            all_posts.extend(ask_filtered)
        except:
            pass
        
        # Remove duplicates
        unique_posts = collector._remove_duplicates(all_posts)
        return unique_posts
    
    def _collect_reddit_data(self, collector, keyword: str, days_back: int, exact_match: bool) -> List:
        """Collect Reddit data with global and subreddit coverage"""
        print("  🔴 Collecting from Reddit (global + subreddits)...")
        
        # Use both global search and subreddit search
        posts = collector.search_keyword(keyword, days_back, exact_match, use_global=True)
        return posts
    
    def _collect_youtube_data(self, collector, keyword: str, days_back: int, exact_match: bool) -> List:
        """Collect YouTube data with comprehensive search"""
        print("  📺 Collecting from YouTube (comprehensive)...")
        
        posts = collector.search_keyword(keyword, days_back, exact_match)
        return posts
    
    def _collect_discord_data(self, collector, keyword: str, days_back: int, exact_match: bool) -> List:
        """Collect Discord data using incremental collection"""
        print("  💬 Collecting from Discord (incremental + historical)...")
        
        # First collect any new data since last collection
        new_posts = collector.collect_new_data(days_back=1)
        print(f"    📅 New posts since last collection: {len(new_posts)}")
        
        # Then search through all data (historical + new) for the keyword
        all_posts = collector.search_keyword(keyword, days_back, exact_match)
        print(f"    🔍 Total posts found for '{keyword}': {len(all_posts)}")
        
        return all_posts
    
    def _check_historical_data(self, keyword: str) -> bool:
        """Check if historical data exists for keyword"""
        keyword_files = []
        for platform in ['hackernews', 'reddit', 'youtube', 'discord']:
            platform_dir = os.path.join(self.historical_dir, platform)
            if os.path.exists(platform_dir):
                # 检查Cache目录中的文件名格式: keyword.json
                cache_file = os.path.join(platform_dir, f"{keyword}.json")
                if os.path.exists(cache_file):
                    keyword_files.append(f"{keyword}.json")
        
        return len(keyword_files) > 0
    
    def _load_historical_data(self, keyword: str, platforms: List[str]) -> Dict[str, Any]:
        """Load existing historical data"""
        from src.analyzers.historical_analyzer import HistoricalAnalyzer
        
        analyzer = HistoricalAnalyzer()
        analysis = analyzer.analyze_keyword_from_historical(keyword)
        
        return {
            'keyword': keyword,
            'collection_time': datetime.now().isoformat(),
            'data_source': 'historical',
            'analysis': analysis
        }
    
    def _save_historical_cache(self, keyword: str, platform: str, posts: List, days_back: int):
        """Save collected data to historical cache"""
        cache_file = os.path.join(
            self.historical_dir, 
            platform, 
            f"{platform}_{keyword.replace(' ', '_')}_{days_back}d.json"
        )
        
        cache_data = {
            'keyword': keyword,
            'platform': platform,
            'collection_date': datetime.now().isoformat(),
            'days_back': days_back,
            'total_posts': len(posts),
            'posts': [post.__dict__ if hasattr(post, '__dict__') else post for post in posts]
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False, default=str)
    
    def _save_collection_summary(self, keyword: str, results: Dict[str, Any]):
        """Save collection summary"""
        summary_file = os.path.join(
            self.data_dir, 
            f"collection_summary_{keyword.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    def _get_date_range(self, posts: List) -> Dict[str, str]:
        """Get date range from posts"""
        if not posts:
            return {'start': None, 'end': None}
        
        timestamps = []
        for post in posts:
            if hasattr(post, 'timestamp'):
                timestamps.append(post.timestamp)
        
        if timestamps:
            return {
                'start': min(timestamps).isoformat(),
                'end': max(timestamps).isoformat()
            }
        
        return {'start': None, 'end': None}
    
    def _get_sample_posts(self, posts: List, limit: int = 3) -> List[Dict]:
        """Get sample posts for preview"""
        samples = []
        for post in posts[:limit]:
            if hasattr(post, '__dict__'):
                sample = {
                    'title': getattr(post, 'title', ''),
                    'author': getattr(post, 'author', ''),
                    'timestamp': getattr(post, 'timestamp', ''),
                    'score': getattr(post, 'score', 0)
                }
                samples.append(sample)
        
        return samples
    
    def get_available_keywords(self) -> List[str]:
        """Get list of available keywords"""
        keywords = set()
        
        for platform in ['hackernews', 'reddit', 'youtube', 'discord']:
            platform_dir = os.path.join(self.historical_dir, platform)
            if os.path.exists(platform_dir):
                for filename in os.listdir(platform_dir):
                    if filename.endswith('.json'):
                        # Cache目录中的文件名格式: keyword.json
                        keyword = filename.replace('.json', '')
                        keywords.add(keyword)
        
        return list(keywords)
    
    def get_keyword_status(self, keyword: str) -> Dict[str, Any]:
        """Get status of keyword data collection"""
        status = {
            'keyword': keyword,
            'has_historical_data': self._check_historical_data(keyword),
            'platforms': {}
        }
        
        for platform in ['hackernews', 'reddit', 'youtube', 'discord']:
            platform_dir = os.path.join(self.historical_dir, platform)
            if os.path.exists(platform_dir):
                # 检查Cache目录中的文件名格式: keyword.json
                cache_file = os.path.join(platform_dir, f"{keyword}.json")
                has_data = os.path.exists(cache_file)
                platform_files = [f"{keyword}.json"] if has_data else []
                status['platforms'][platform] = {
                    'has_data': has_data,
                    'files': platform_files
                }
        
        return status

def main():
    parser = argparse.ArgumentParser(description='BuzzScope Data Collection Service')
    parser.add_argument('keyword', help='Keyword to collect data for')
    parser.add_argument('--days', type=int, default=30, help='Days to look back (default: 30)')
    parser.add_argument('--platforms', nargs='+', 
                       choices=['hackernews', 'reddit', 'youtube', 'discord'],
                       help='Platforms to collect from (default: all)')
    parser.add_argument('--exact-match', action='store_true', 
                       help='Use exact phrase matching')
    parser.add_argument('--no-historical', action='store_true',
                       help='Skip historical data check')
    
    args = parser.parse_args()
    
    # Initialize service
    service = DataCollectionService()
    
    # Collect data
    results = service.collect_keyword_data(
        keyword=args.keyword,
        days_back=args.days,
        platforms=args.platforms,
        exact_match=args.exact_match,
        use_historical=not args.no_historical
    )
    
    print(f"\n📁 Data saved to: ./data/")
    print(f"🎯 Keyword '{args.keyword}' is now ready for analysis!")

if __name__ == "__main__":
    main()
