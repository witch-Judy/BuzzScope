"""
Historical data collector for building keyword databases
"""
import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class HistoricalCollector:
    """Collector for building historical keyword databases"""
    
    def __init__(self):
        self.data_dir = './data/historical'
        self.keywords = ['unified namespace', 'iot', 'mqtt', 'ai']
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize YouTube API if available
        youtube_key = os.getenv('YOUTUBE_API_KEY')
        if youtube_key:
            self.youtube = build('youtube', 'v3', developerKey=youtube_key)
        else:
            self.youtube = None
    
    def collect_hackernews_historical(self, keyword: str, days_back: int = 365) -> Dict[str, Any]:
        """
        Collect Hacker News historical data for a keyword
        
        Strategy: Iterate through story IDs to find historical mentions
        """
        print(f"Collecting HN historical data for '{keyword}' ({days_back} days back)")
        
        # Calculate target date range
        target_date = datetime.now() - timedelta(days=days_back)
        
        # Start from a reasonable ID range (adjust based on HN's current ID range)
        # HN IDs are roughly sequential, so we can estimate ranges
        current_max_id = 45400000  # Approximate current max ID
        days_per_id = 365 / (current_max_id - 40000000)  # Rough estimate
        start_id = max(1, current_max_id - int(days_back / days_per_id))
        
        collected_posts = []
        checked_ids = 0
        found_posts = 0
        
        # Sample IDs in the range (don't check every single ID)
        step = max(1, (current_max_id - start_id) // 10000)  # Check every Nth ID
        
        for story_id in range(start_id, current_max_id, step):
            try:
                response = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
                if response.status_code == 200:
                    data = response.json()
                    if data and data.get('type') in ['story', 'comment']:
                        # Check if keyword is mentioned
                        title = data.get('title', '').lower()
                        text = data.get('text', '').lower()
                        keyword_lower = keyword.lower()
                        
                        if keyword_lower in title or keyword_lower in text:
                            # Check if within date range
                            post_time = datetime.fromtimestamp(data.get('time', 0))
                            if post_time >= target_date:
                                collected_posts.append({
                                    'id': story_id,
                                    'title': data.get('title', ''),
                                    'text': data.get('text', ''),
                                    'author': data.get('by', ''),
                                    'time': post_time.isoformat(),
                                    'score': data.get('score', 0),
                                    'type': data.get('type', 'story'),
                                    'url': data.get('url', '')
                                })
                                found_posts += 1
                
                checked_ids += 1
                if checked_ids % 100 == 0:
                    print(f"  Checked {checked_ids} IDs, found {found_posts} posts")
                    time.sleep(0.1)  # Rate limiting
                
                if found_posts >= 1000:  # Limit to prevent excessive collection
                    break
                    
            except Exception as e:
                print(f"Error checking ID {story_id}: {e}")
                continue
        
        # Save collected data
        filename = f"hn_historical_{keyword.replace(' ', '_')}_{days_back}d.json"
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'keyword': keyword,
                'collection_date': datetime.now().isoformat(),
                'days_back': days_back,
                'total_posts': len(collected_posts),
                'posts': collected_posts
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Collected {len(collected_posts)} HN posts for '{keyword}'")
        return {
            'keyword': keyword,
            'platform': 'hackernews',
            'posts_collected': len(collected_posts),
            'file_saved': filepath
        }
    
    def collect_reddit_historical(self, keyword: str, days_back: int = 365) -> Dict[str, Any]:
        """
        Collect Reddit historical data for a keyword using search API
        """
        print(f"Collecting Reddit historical data for '{keyword}' ({days_back} days back)")
        
        headers = {
            'User-Agent': 'BuzzScope/1.0 (Historical Data Collection)'
        }
        
        collected_posts = []
        
        # Try different time ranges
        time_ranges = ['year', 'month', 'week', 'day']
        
        for time_range in time_ranges:
            try:
                url = 'https://www.reddit.com/search.json'
                params = {
                    'q': keyword,
                    'sort': 'new',
                    'limit': 100,
                    't': time_range
                }
                
                response = requests.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])
                    
                    for post in posts:
                        post_data = post['data']
                        created_utc = post_data.get('created_utc', 0)
                        post_time = datetime.fromtimestamp(created_utc)
                        
                        # Check if within our target date range
                        target_date = datetime.now() - timedelta(days=days_back)
                        if post_time >= target_date:
                            collected_posts.append({
                                'id': post_data.get('id', ''),
                                'title': post_data.get('title', ''),
                                'selftext': post_data.get('selftext', ''),
                                'author': post_data.get('author', ''),
                                'subreddit': post_data.get('subreddit', ''),
                                'created_utc': created_utc,
                                'time': post_time.isoformat(),
                                'score': post_data.get('score', 0),
                                'num_comments': post_data.get('num_comments', 0),
                                'url': post_data.get('url', ''),
                                'permalink': post_data.get('permalink', '')
                            })
                    
                    print(f"  {time_range}: Found {len(posts)} posts")
                    time.sleep(1)  # Rate limiting
                    
            except Exception as e:
                print(f"Error collecting {time_range} data: {e}")
                continue
        
        # Remove duplicates based on post ID
        unique_posts = {}
        for post in collected_posts:
            unique_posts[post['id']] = post
        
        collected_posts = list(unique_posts.values())
        
        # Save collected data
        filename = f"reddit_historical_{keyword.replace(' ', '_')}_{days_back}d.json"
        filepath = os.path.join(self.data_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'keyword': keyword,
                'collection_date': datetime.now().isoformat(),
                'days_back': days_back,
                'total_posts': len(collected_posts),
                'posts': collected_posts
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Collected {len(collected_posts)} Reddit posts for '{keyword}'")
        return {
            'keyword': keyword,
            'platform': 'reddit',
            'posts_collected': len(collected_posts),
            'file_saved': filepath
        }
    
    def collect_youtube_historical(self, keyword: str, days_back: int = 365) -> Dict[str, Any]:
        """
        Collect YouTube historical data for a keyword
        """
        if not self.youtube:
            print("YouTube API not configured, skipping YouTube collection")
            return {'error': 'YouTube API not configured'}
        
        print(f"Collecting YouTube historical data for '{keyword}' ({days_back} days back)")
        
        target_date = datetime.now() - timedelta(days=days_back)
        collected_videos = []
        
        try:
            # Search for videos
            search_response = self.youtube.search().list(
                q=keyword,
                part='id,snippet',
                type='video',
                order='relevance',
                publishedAfter=target_date.isoformat() + 'Z',
                maxResults=200  # Maximum allowed
            ).execute()
            
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if video_ids:
                # Get detailed video information
                videos_response = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(video_ids)
                ).execute()
                
                for video in videos_response.get('items', []):
                    snippet = video['snippet']
                    statistics = video.get('statistics', {})
                    
                    collected_videos.append({
                        'video_id': video['id'],
                        'title': snippet['title'],
                        'description': snippet.get('description', '')[:1000],
                        'channel_title': snippet['channelTitle'],
                        'channel_id': snippet['channelId'],
                        'published_at': snippet['publishedAt'],
                        'view_count': int(statistics.get('viewCount', 0)),
                        'like_count': int(statistics.get('likeCount', 0)),
                        'comment_count': int(statistics.get('commentCount', 0)),
                        'duration': video.get('contentDetails', {}).get('duration', ''),
                        'url': f"https://www.youtube.com/watch?v={video['id']}"
                    })
            
            # Save collected data
            filename = f"youtube_historical_{keyword.replace(' ', '_')}_{days_back}d.json"
            filepath = os.path.join(self.data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'keyword': keyword,
                    'collection_date': datetime.now().isoformat(),
                    'days_back': days_back,
                    'total_videos': len(collected_videos),
                    'videos': collected_videos
                }, f, indent=2, ensure_ascii=False)
            
            print(f"Collected {len(collected_videos)} YouTube videos for '{keyword}'")
            return {
                'keyword': keyword,
                'platform': 'youtube',
                'videos_collected': len(collected_videos),
                'file_saved': filepath
            }
            
        except Exception as e:
            print(f"Error collecting YouTube data: {e}")
            return {'error': str(e)}
    
    def build_keyword_database(self, keywords: List[str] = None, days_back: int = 365) -> Dict[str, Any]:
        """
        Build historical database for multiple keywords
        """
        if keywords is None:
            keywords = self.keywords
        
        print(f"Building historical database for keywords: {keywords}")
        print(f"Time range: {days_back} days back")
        
        results = {}
        
        for keyword in keywords:
            print(f"\n=== Collecting data for '{keyword}' ===")
            
            keyword_results = {}
            
            # Collect from each platform
            try:
                hn_result = self.collect_hackernews_historical(keyword, days_back)
                keyword_results['hackernews'] = hn_result
            except Exception as e:
                print(f"Error collecting HN data for '{keyword}': {e}")
                keyword_results['hackernews'] = {'error': str(e)}
            
            try:
                reddit_result = self.collect_reddit_historical(keyword, days_back)
                keyword_results['reddit'] = reddit_result
            except Exception as e:
                print(f"Error collecting Reddit data for '{keyword}': {e}")
                keyword_results['reddit'] = {'error': str(e)}
            
            try:
                youtube_result = self.collect_youtube_historical(keyword, days_back)
                keyword_results['youtube'] = youtube_result
            except Exception as e:
                print(f"Error collecting YouTube data for '{keyword}': {e}")
                keyword_results['youtube'] = {'error': str(e)}
            
            results[keyword] = keyword_results
            
            # Add delay between keywords to respect rate limits
            time.sleep(5)
        
        # Save summary
        summary_file = os.path.join(self.data_dir, f'collection_summary_{days_back}d.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'collection_date': datetime.now().isoformat(),
                'days_back': days_back,
                'keywords': keywords,
                'results': results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== Collection Complete ===")
        print(f"Summary saved to: {summary_file}")
        
        return results
