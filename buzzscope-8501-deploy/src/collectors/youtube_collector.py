"""
YouTube data collector using YouTube Data API v3
"""
from googleapiclient.discovery import build
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .base_collector import BaseCollector
from ..models import YouTubePost
from ..config import Config

class YouTubeCollector(BaseCollector):
    """Collector for YouTube data using YouTube Data API v3"""
    
    def __init__(self):
        super().__init__("youtube")
        
        # Initialize YouTube API client
        if Config.is_platform_enabled('youtube'):
            self.youtube = build('youtube', 'v3', developerKey=Config.YOUTUBE_API_KEY)
            self.max_results = Config.get_platform_config('youtube').get('max_results', 50)
        else:
            self.youtube = None
            self.logger.warning("YouTube API not configured. Set YOUTUBE_API_KEY in .env")
    
    def search_keyword(self, keyword: str, days_back: int = 30, exact_match: bool = False) -> List[YouTubePost]:
        """Search YouTube for keyword mentions"""
        if not Config.is_platform_enabled('youtube'):
            self.logger.warning("YouTube API not configured")
            return []
        
        self.logger.info(f"Searching YouTube for keyword: {keyword} (exact_match={exact_match})")
        
        posts = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        try:
            # Search for videos
            search_response = self.youtube.search().list(
                q=keyword,
                part='id,snippet',
                type='video',
                order='relevance',
                publishedAfter=cutoff_date.isoformat() + 'Z',
                maxResults=self.max_results
            ).execute()
            
            # Get video details for each result
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if video_ids:
                # Get detailed video information
                videos_response = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(video_ids)
                ).execute()
                
                for video in videos_response.get('items', []):
                    post = self._convert_video(video)
                    if post:
                        posts.append(post)
            
            # Apply exact match filtering if requested
            if exact_match and posts:
                posts = self.extract_keyword_mentions(posts, keyword, exact_match=True)
            
            self.logger.info(f"Found {len(posts)} videos mentioning '{keyword}'")
            
        except Exception as e:
            self.logger.error(f"Error searching YouTube: {e}")
        
        return self.clean_posts(posts)
    
    def get_recent_posts(self, limit: int = 100) -> List[YouTubePost]:
        """Get recent videos from tech channels"""
        if not Config.is_platform_enabled('youtube'):
            self.logger.warning("YouTube API not configured")
            return []
        
        self.logger.info(f"Getting {limit} recent videos from YouTube")
        
        posts = []
        
        # Tech-related search terms for recent content
        tech_terms = ['technology', 'programming', 'IoT', 'arduino', 'machine learning', 'AI']
        
        for term in tech_terms:
            try:
                # Ensure we get at least 1 result per term
                max_results = max(1, limit // len(tech_terms))
                search_response = self.youtube.search().list(
                    q=term,
                    part='id,snippet',
                    type='video',
                    order='date',
                    maxResults=max_results
                ).execute()
                
                video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                
                if video_ids:
                    videos_response = self.youtube.videos().list(
                        part='snippet,statistics,contentDetails',
                        id=','.join(video_ids)
                    ).execute()
                    
                    for video in videos_response.get('items', []):
                        post = self._convert_video(video)
                        if post:
                            posts.append(post)
                            
            except Exception as e:
                self.logger.error(f"Error getting recent videos for term '{term}': {e}")
                continue
        
        return posts[:limit]
    
    def _convert_video(self, video: Dict[str, Any]) -> YouTubePost:
        """Convert YouTube API video data to YouTubePost"""
        try:
            snippet = video['snippet']
            statistics = video.get('statistics', {})
            content_details = video.get('contentDetails', {})
            
            # Parse published date
            published_at = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
            
            # Get video URL
            video_url = f"https://www.youtube.com/watch?v={video['id']}"
            
            # Extract description (first 1000 chars)
            description = snippet.get('description', '')[:1000]
            
            return YouTubePost(
                platform="youtube",
                post_id=video['id'],
                title=snippet['title'],
                content=description,
                author=snippet['channelTitle'],
                timestamp=published_at,
                url=video_url,
                video_id=video['id'],
                channel_id=snippet['channelId'],
                view_count=int(statistics.get('viewCount', 0)),
                like_count=int(statistics.get('likeCount', 0)),
                comment_count=int(statistics.get('commentCount', 0)),
                duration=content_details.get('duration'),
                metadata={
                    'category_id': snippet.get('categoryId'),
                    'tags': snippet.get('tags', []),
                    'thumbnails': snippet.get('thumbnails', {}),
                    'default_language': snippet.get('defaultLanguage'),
                    'live_broadcast_content': snippet.get('liveBroadcastContent')
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error converting video {video.get('id', 'unknown')}: {e}")
            return None
