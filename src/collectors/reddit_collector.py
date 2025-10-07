"""
Reddit data collector using Reddit's public JSON API
"""
import requests
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .base_collector import BaseCollector
from ..models import RedditPost
from ..config import Config

class RedditCollector(BaseCollector):
    """Collector for Reddit data using Reddit's public JSON API"""

    def __init__(self):
        super().__init__("reddit")

        # Reddit's public JSON API endpoints
        self.reddit_base_url = "https://www.reddit.com"
        self.reddit_json_url = "https://www.reddit.com/r"

        # Get subreddits to search
        self.subreddits = Config.get_platform_config('reddit').get('subreddits', [
            'technology', 'programming', 'MachineLearning', 'artificial',
            'datascience', 'IoT', 'cybersecurity', 'startups'
        ])

        self.logger.info(f"Reddit collector initialized with Reddit's public JSON API")

    def search_keyword(self, keyword: str, days_back: int = 30, exact_match: bool = False, use_global: bool = True) -> List[RedditPost]:
        """Search Reddit for keyword mentions using Reddit's public JSON API"""
        self.logger.info(f"Searching Reddit for keyword: {keyword} (exact_match={exact_match}, global={use_global})")

        posts = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        if use_global:
            # Global search across r/all
            posts.extend(self._search_global(keyword, cutoff_date, exact_match))
        
        # Search across configured subreddits
        for subreddit_name in self.subreddits:
            try:
                # Get recent posts from subreddit
                url = f"{self.reddit_json_url}/{subreddit_name}/new.json"
                params = {'limit': 100}

                headers = {
                    'User-Agent': 'BuzzScope/1.0 (Educational Research Tool)'
                }

                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()

                data = response.json()
                submissions = data.get('data', {}).get('children', [])

                for child in submissions:
                    submission = child.get('data', {})
                    post = self._convert_submission(submission, keyword, exact_match, cutoff_date)
                    if post:
                        posts.append(post)

                self.logger.info(f"Found {len(submissions)} posts in r/{subreddit_name}")

                # Rate limiting
                time.sleep(1)

            except Exception as e:
                self.logger.error(f"Error searching subreddit {subreddit_name}: {e}")
                continue

        self.logger.info(f"Found {len(posts)} Reddit posts mentioning '{keyword}'")
        return self.clean_posts(posts)
    
    def _search_global(self, keyword: str, cutoff_date: datetime, exact_match: bool = False) -> List[RedditPost]:
        """Search Reddit globally for keyword mentions using search API"""
        posts = []
        
        try:
            # Use Reddit's search API
            url = f"{self.reddit_base_url}/search.json"
            params = {
                'q': keyword,
                'sort': 'relevance',
                't': 'all',  # All time
                'limit': 100
            }
            
            headers = {
                'User-Agent': 'BuzzScope/1.0 (Educational Research Tool)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            submissions = data.get('data', {}).get('children', [])
            
            for child in submissions:
                submission = child.get('data', {})
                post = self._convert_submission(submission, keyword, exact_match, cutoff_date)
                if post:
                    posts.append(post)
            
            self.logger.info(f"Found {len(posts)} posts in global search")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            self.logger.error(f"Error in global search: {e}")
        
        return posts

    def get_recent_posts(self, limit: int = 50) -> List[RedditPost]:
        """Get recent posts from Reddit"""
        self.logger.info(f"Getting {limit} recent Reddit posts")

        posts = []

        try:
            # Get recent posts from r/all
            url = f"{self.reddit_base_url}/r/all/new.json"
            params = {'limit': limit}

            headers = {
                'User-Agent': 'BuzzScope/1.0 (Educational Research Tool)'
            }

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            submissions = data.get('data', {}).get('children', [])

            for child in submissions:
                submission = child.get('data', {})
                post = self._convert_submission(submission)
                if post:
                    posts.append(post)

            self.logger.info(f"Retrieved {len(posts)} recent Reddit posts")

        except Exception as e:
            self.logger.error(f"Error getting recent Reddit posts: {e}")

        return posts

    def _convert_submission(self, submission: Dict[str, Any], keyword: str = None, exact_match: bool = False, cutoff_date: datetime = None) -> RedditPost:
        """Convert Reddit submission to RedditPost"""
        try:
            # Extract basic data
            post_id = submission.get('id', '')
            title = submission.get('title', '')
            content = submission.get('selftext', '')
            author = submission.get('author', 'Unknown')
            subreddit = submission.get('subreddit', '')

            # Parse timestamp
            created_utc = submission.get('created_utc', 0)
            timestamp = datetime.fromtimestamp(created_utc)

            # Check if post is within date range
            if cutoff_date and timestamp < cutoff_date:
                return None

            # Build URL
            permalink = submission.get('permalink', '')
            url = f"https://reddit.com{permalink}" if permalink else ''

            # Extract metrics
            score = submission.get('score', 0)
            num_comments = submission.get('num_comments', 0)
            upvote_ratio = submission.get('upvote_ratio', 0)

            # Check if keyword is mentioned (if keyword provided)
            if keyword:
                keyword_lower = keyword.lower()
                title_lower = title.lower()
                content_lower = content.lower()

                if exact_match:
                    # Use exact phrase matching
                    if not (self._exact_phrase_match(title_lower, keyword_lower) or
                           self._exact_phrase_match(content_lower, keyword_lower)):
                        return None
                else:
                    # Use substring matching
                    if not (keyword_lower in title_lower or keyword_lower in content_lower):
                        return None

            return RedditPost(
                platform="reddit",
                post_id=post_id,
                title=title,
                content=content,
                author=author,
                timestamp=timestamp,
                url=url,
                subreddit=subreddit,
                score=score,
                num_comments=num_comments,
                upvote_ratio=upvote_ratio,
                metadata={
                    'domain': submission.get('domain', ''),
                    'is_self': submission.get('is_self', False),
                    'over_18': submission.get('over_18', False),
                    'spoiler': submission.get('spoiler', False),
                    'stickied': submission.get('stickied', False)
                }
            )

        except Exception as e:
            self.logger.error(f"Error converting Reddit submission: {e}")
            return None