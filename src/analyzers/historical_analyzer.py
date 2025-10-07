"""
Historical data analyzer for keyword databases
"""
import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base_analyzer import BaseAnalyzer
from ..models import KeywordMetrics

class HistoricalAnalyzer(BaseAnalyzer):
    """Analyzer for historical keyword data"""
    
    def __init__(self):
        super().__init__("historical")
        self.historical_data_dir = './data/historical'
    
    def analyze_keyword_from_historical(self, keyword: str, platform: str = None) -> Dict[str, Any]:
        """
        Analyze keyword using historical data
        
        Args:
            keyword: Keyword to analyze
            platform: Specific platform to analyze (optional)
            
        Returns:
            Analysis results
        """
        print(f"Analyzing historical data for '{keyword}'")
        
        analysis = {
            'keyword': keyword,
            'analysis_date': datetime.now().isoformat(),
            'platforms': {},
            'summary': {}
        }
        
        # Find historical data files for this keyword
        keyword_files = self._find_keyword_files(keyword)
        
        if not keyword_files:
            return {
                'keyword': keyword,
                'error': f'No historical data found for keyword: {keyword}',
                'available_keywords': self._get_available_keywords()
            }
        
        # Analyze each platform's data
        for platform, filepath in keyword_files.items():
            if platform == 'hackernews':
                platform_data = self._analyze_hackernews_historical(filepath)
            elif platform == 'reddit':
                platform_data = self._analyze_reddit_historical(filepath)
            elif platform == 'youtube':
                platform_data = self._analyze_youtube_historical(filepath)
            else:
                continue
            
            analysis['platforms'][platform] = platform_data
        
        # Generate cross-platform summary
        analysis['summary'] = self._generate_cross_platform_summary(analysis['platforms'])
        
        return analysis
    
    def _find_keyword_files(self, keyword: str) -> Dict[str, str]:
        """Find historical data files for a keyword"""
        keyword_files = {}
        
        if not os.path.exists(self.historical_data_dir):
            return keyword_files
        
        # Search for files containing the keyword
        for filename in os.listdir(self.historical_data_dir):
            if keyword.replace(' ', '_') in filename and filename.endswith('.json'):
                # Extract platform from filename
                if filename.startswith('hn_historical_'):
                    platform = 'hackernews'
                elif filename.startswith('reddit_historical_'):
                    platform = 'reddit'
                elif filename.startswith('youtube_historical_'):
                    platform = 'youtube'
                else:
                    continue
                
                filepath = os.path.join(self.historical_data_dir, filename)
                keyword_files[platform] = filepath
        
        return keyword_files
    
    def _analyze_hackernews_historical(self, filepath: str) -> Dict[str, Any]:
        """Analyze Hacker News historical data"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        posts = data.get('posts', [])
        if not posts:
            return {'error': 'No posts found'}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(posts)
        df['time'] = pd.to_datetime(df['time'])
        
        # Calculate metrics
        total_posts = len(df)
        unique_authors = df['author'].nunique()
        total_score = df['score'].sum()
        avg_score = df['score'].mean()
        
        # Time analysis
        date_range = (df['time'].min(), df['time'].max())
        days_span = (date_range[1] - date_range[0]).days
        
        # Content type analysis
        type_counts = df['type'].value_counts().to_dict()
        
        # Top posts
        top_posts = df.nlargest(5, 'score')[['title', 'author', 'score', 'time']].to_dict('records')
        
        # Daily activity
        daily_activity = df.groupby(df['time'].dt.date).size().to_dict()
        
        return {
            'total_posts': total_posts,
            'unique_authors': unique_authors,
            'total_score': int(total_score),
            'avg_score': float(avg_score),
            'date_range': [date_range[0].isoformat(), date_range[1].isoformat()],
            'days_span': days_span,
            'content_types': type_counts,
            'top_posts': top_posts,
            'daily_activity': daily_activity
        }
    
    def _analyze_reddit_historical(self, filepath: str) -> Dict[str, Any]:
        """Analyze Reddit historical data"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        posts = data.get('posts', [])
        if not posts:
            return {'error': 'No posts found'}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(posts)
        df['time'] = pd.to_datetime(df['time'])
        
        # Calculate metrics
        total_posts = len(df)
        unique_authors = df['author'].nunique()
        total_score = df['score'].sum()
        avg_score = df['score'].mean()
        total_comments = df['num_comments'].sum()
        
        # Subreddit analysis
        subreddit_counts = df['subreddit'].value_counts().to_dict()
        
        # Time analysis
        date_range = (df['time'].min(), df['time'].max())
        days_span = (date_range[1] - date_range[0]).days
        
        # Top posts
        top_posts = df.nlargest(5, 'score')[['title', 'subreddit', 'author', 'score', 'num_comments']].to_dict('records')
        
        # Daily activity
        daily_activity = df.groupby(df['time'].dt.date).size().to_dict()
        
        return {
            'total_posts': total_posts,
            'unique_authors': unique_authors,
            'total_score': int(total_score),
            'avg_score': float(avg_score),
            'total_comments': int(total_comments),
            'date_range': [date_range[0].isoformat(), date_range[1].isoformat()],
            'days_span': days_span,
            'subreddits': subreddit_counts,
            'top_posts': top_posts,
            'daily_activity': daily_activity
        }
    
    def _analyze_youtube_historical(self, filepath: str) -> Dict[str, Any]:
        """Analyze YouTube historical data"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        videos = data.get('videos', [])
        if not videos:
            return {'error': 'No videos found'}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(videos)
        df['published_at'] = pd.to_datetime(df['published_at'])
        
        # Calculate metrics
        total_videos = len(df)
        unique_channels = df['channel_title'].nunique()
        total_views = df['view_count'].sum()
        total_likes = df['like_count'].sum()
        total_comments = df['comment_count'].sum()
        
        # Channel analysis
        channel_counts = df['channel_title'].value_counts().to_dict()
        
        # Time analysis
        date_range = (df['published_at'].min(), df['published_at'].max())
        days_span = (date_range[1] - date_range[0]).days
        
        # Top videos
        top_videos = df.nlargest(5, 'view_count')[['title', 'channel_title', 'view_count', 'like_count', 'published_at']].to_dict('records')
        
        # Daily activity
        daily_activity = df.groupby(df['published_at'].dt.date).size().to_dict()
        
        return {
            'total_videos': total_videos,
            'unique_channels': unique_channels,
            'total_views': int(total_views),
            'total_likes': int(total_likes),
            'total_comments': int(total_comments),
            'avg_views': float(total_views / total_videos) if total_videos > 0 else 0,
            'date_range': [date_range[0].isoformat(), date_range[1].isoformat()],
            'days_span': days_span,
            'top_channels': channel_counts,
            'top_videos': top_videos,
            'daily_activity': daily_activity
        }
    
    def _generate_cross_platform_summary(self, platforms_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate cross-platform summary"""
        summary = {
            'total_platforms': len(platforms_data),
            'total_mentions': 0,
            'total_authors': 0,
            'total_engagement': 0,
            'platform_comparison': {}
        }
        
        for platform, data in platforms_data.items():
            if 'error' in data:
                continue
            
            if platform == 'hackernews':
                mentions = data.get('total_posts', 0)
                authors = data.get('unique_authors', 0)
                engagement = data.get('total_score', 0)
            elif platform == 'reddit':
                mentions = data.get('total_posts', 0)
                authors = data.get('unique_authors', 0)
                engagement = data.get('total_score', 0) + data.get('total_comments', 0)
            elif platform == 'youtube':
                mentions = data.get('total_videos', 0)
                authors = data.get('unique_channels', 0)
                engagement = data.get('total_views', 0)
            else:
                continue
            
            summary['total_mentions'] += mentions
            summary['total_authors'] += authors
            summary['total_engagement'] += engagement
            
            summary['platform_comparison'][platform] = {
                'mentions': mentions,
                'authors': authors,
                'engagement': engagement
            }
        
        return summary
    
    def _get_available_keywords(self) -> List[str]:
        """Get list of available keywords in historical data"""
        keywords = set()
        
        if not os.path.exists(self.historical_data_dir):
            return list(keywords)
        
        for filename in os.listdir(self.historical_data_dir):
            if filename.endswith('.json'):
                # Extract keyword from filename
                parts = filename.split('_')
                if len(parts) >= 3:
                    keyword = parts[2].replace('_', ' ')
                    keywords.add(keyword)
        
        return list(keywords)
    
    def get_historical_data_status(self) -> Dict[str, Any]:
        """Get status of historical data collection"""
        status = {
            'data_directory': self.historical_data_dir,
            'exists': os.path.exists(self.historical_data_dir),
            'available_keywords': self._get_available_keywords(),
            'files': []
        }
        
        if os.path.exists(self.historical_data_dir):
            for filename in os.listdir(self.historical_data_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.historical_data_dir, filename)
                    file_size = os.path.getsize(filepath)
                    status['files'].append({
                        'filename': filename,
                        'size_bytes': file_size,
                        'size_mb': round(file_size / 1024 / 1024, 2)
                    })
        
        return status
    
    # Required abstract methods from BaseAnalyzer
    def calculate_metrics(self, df, keyword, start_date, end_date):
        """Required abstract method - not used in historical analysis"""
        pass
    
    def calculate_interactions(self, df):
        """Required abstract method - not used in historical analysis"""
        return 0
    
    def get_top_contributors(self, df, limit=10):
        """Required abstract method - not used in historical analysis"""
        return []
    
    def get_sample_posts(self, df, limit=5):
        """Required abstract method - not used in historical analysis"""
        return []
