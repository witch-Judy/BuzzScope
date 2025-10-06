"""
Storage system for BuzzScope using Parquet format
"""
import os
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union
import logging
from pathlib import Path
from .models import BasePost, PLATFORM_MODELS
from .config import Config

logger = logging.getLogger(__name__)

class BuzzScopeStorage:
    """Storage manager for BuzzScope data using Parquet format"""
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir or Config.DATA_DIR)
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create platform-specific directories
        for platform in PLATFORM_MODELS.keys():
            (self.data_dir / platform).mkdir(exist_ok=True)
        
        # Create analysis results directory
        (self.data_dir / 'analysis').mkdir(exist_ok=True)
    
    def save_posts(self, posts: List[BasePost], platform: str, 
                   partition_date: Optional[date] = None) -> str:
        """
        Save posts to Parquet file with partitioning
        
        Args:
            posts: List of posts to save
            platform: Platform name (hackernews, reddit, etc.)
            partition_date: Date for partitioning (defaults to today)
            
        Returns:
            Path to saved file
        """
        if not posts:
            logger.warning(f"No posts to save for platform {platform}")
            return ""
        
        if partition_date is None:
            partition_date = date.today()
        
        # Convert posts to DataFrame
        df = self._posts_to_dataframe(posts)
        
        # Create file path with partitioning
        file_path = self._get_file_path(platform, partition_date)
        
        # Save to Parquet
        try:
            df.to_parquet(file_path, index=False, compression='snappy')
            logger.info(f"Saved {len(posts)} posts to {file_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving posts to {file_path}: {e}")
            raise
    
    def load_posts(self, platform: str, start_date: Optional[date] = None, 
                   end_date: Optional[date] = None) -> pd.DataFrame:
        """
        Load posts from storage
        
        Args:
            platform: Platform name
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            DataFrame with posts
        """
        platform_dir = self.data_dir / platform
        
        if not platform_dir.exists():
            logger.warning(f"No data directory found for platform {platform}")
            return pd.DataFrame()
        
        # Find all Parquet files for the platform
        parquet_files = list(platform_dir.glob("*.parquet"))
        
        if not parquet_files:
            logger.warning(f"No Parquet files found for platform {platform}")
            return pd.DataFrame()
        
        # Load and combine all files
        dfs = []
        for file_path in parquet_files:
            try:
                df = pd.read_parquet(file_path)
                dfs.append(df)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
                continue
        
        if not dfs:
            return pd.DataFrame()
        
        # Combine all DataFrames
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Convert timestamp column to datetime
        if 'timestamp' in combined_df.columns:
            combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
        
        # Filter by date range if specified
        if start_date or end_date:
            if 'timestamp' in combined_df.columns:
                if start_date:
                    combined_df = combined_df[combined_df['timestamp'].dt.date >= start_date]
                if end_date:
                    combined_df = combined_df[combined_df['timestamp'].dt.date <= end_date]
        
        logger.info(f"Loaded {len(combined_df)} posts for platform {platform}")
        return combined_df
    
    def search_posts(self, keyword: str, platforms: Optional[List[str]] = None,
                     start_date: Optional[date] = None, 
                     end_date: Optional[date] = None,
                     exact_match: bool = False) -> Dict[str, pd.DataFrame]:
        """
        Search for posts containing keyword across platforms
        
        Args:
            keyword: Keyword to search for
            platforms: List of platforms to search (defaults to all)
            start_date: Start date for filtering
            end_date: End date for filtering
            exact_match: If True, use exact phrase matching. If False, use substring matching.
            
        Returns:
            Dictionary mapping platform names to DataFrames of matching posts
        """
        if platforms is None:
            platforms = list(PLATFORM_MODELS.keys())
        
        results = {}
        keyword_lower = keyword.lower()
        
        for platform in platforms:
            try:
                df = self.load_posts(platform, start_date, end_date)
                
                if df.empty:
                    continue
                
                # Search in title and content columns
                if exact_match:
                    # Use regex for exact phrase matching
                    import re
                    escaped_keyword = re.escape(keyword_lower)
                    pattern = r'\b' + escaped_keyword + r'\b'
                    mask = (
                        df['title'].str.lower().str.contains(pattern, regex=True, na=False) |
                        df['content'].str.lower().str.contains(pattern, regex=True, na=False)
                    )
                else:
                    # Use substring matching
                    mask = (
                        df['title'].str.lower().str.contains(keyword_lower, na=False) |
                        df['content'].str.lower().str.contains(keyword_lower, na=False)
                    )
                
                matching_posts = df[mask]
                if not matching_posts.empty:
                    results[platform] = matching_posts
                    logger.info(f"Found {len(matching_posts)} posts mentioning '{keyword}' in {platform}")
                
            except Exception as e:
                logger.error(f"Error searching {platform} for '{keyword}': {e}")
                continue
        
        return results
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about stored data"""
        stats = {
            'total_platforms': 0,
            'platform_stats': {},
            'total_posts': 0,
            'date_range': None
        }
        
        all_timestamps = []
        
        for platform in PLATFORM_MODELS.keys():
            platform_dir = self.data_dir / platform
            if not platform_dir.exists():
                continue
            
            parquet_files = list(platform_dir.glob("*.parquet"))
            if not parquet_files:
                continue
            
            platform_posts = 0
            platform_timestamps = []
            
            for file_path in parquet_files:
                try:
                    df = pd.read_parquet(file_path)
                    platform_posts += len(df)
                    
                    if 'timestamp' in df.columns:
                        timestamps = pd.to_datetime(df['timestamp'])
                        platform_timestamps.extend(timestamps.tolist())
                        all_timestamps.extend(timestamps.tolist())
                        
                except Exception as e:
                    logger.error(f"Error reading stats from {file_path}: {e}")
                    continue
            
            if platform_posts > 0:
                stats['platform_stats'][platform] = {
                    'total_posts': platform_posts,
                    'files': len(parquet_files),
                    'date_range': (
                        min(platform_timestamps).date() if platform_timestamps else None,
                        max(platform_timestamps).date() if platform_timestamps else None
                    )
                }
                stats['total_platforms'] += 1
                stats['total_posts'] += platform_posts
        
        if all_timestamps:
            # Handle timezone-aware and timezone-naive timestamps
            try:
                stats['date_range'] = (
                    min(all_timestamps).date(),
                    max(all_timestamps).date()
                )
            except TypeError:
                # If there's a timezone mismatch, convert all to naive
                naive_timestamps = [ts.tz_localize(None) if ts.tz is not None else ts for ts in all_timestamps]
                stats['date_range'] = (
                    min(naive_timestamps).date(),
                    max(naive_timestamps).date()
                )
        
        return stats
    
    def save_analysis_results(self, results: Dict[str, Any], 
                             analysis_name: str) -> str:
        """Save analysis results to storage"""
        analysis_dir = self.data_dir / 'analysis'
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{analysis_name}_{timestamp}.parquet"
        file_path = analysis_dir / filename
        
        try:
            # Convert results to DataFrame if needed
            if isinstance(results, dict):
                df = pd.DataFrame([results])
            else:
                df = results
            
            df.to_parquet(file_path, index=False)
            logger.info(f"Saved analysis results to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error saving analysis results: {e}")
            raise
    
    def _posts_to_dataframe(self, posts: List[BasePost]) -> pd.DataFrame:
        """Convert list of posts to DataFrame"""
        data = []
        for post in posts:
            post_dict = post.to_dict()
            data.append(post_dict)
        
        return pd.DataFrame(data)
    
    def _get_file_path(self, platform: str, partition_date: date) -> Path:
        """Get file path for storing posts with partitioning"""
        platform_dir = self.data_dir / platform
        filename = f"{platform}_{partition_date.strftime('%Y%m%d')}.parquet"
        return platform_dir / filename
    
    def cleanup_old_files(self, days_to_keep: int = 90):
        """Clean up old Parquet files to save space"""
        cutoff_date = datetime.now().date() - pd.Timedelta(days=days_to_keep)
        
        for platform in PLATFORM_MODELS.keys():
            platform_dir = self.data_dir / platform
            if not platform_dir.exists():
                continue
            
            for file_path in platform_dir.glob("*.parquet"):
                try:
                    # Extract date from filename
                    filename = file_path.stem
                    date_str = filename.split('_')[-1]  # Get date part
                    file_date = datetime.strptime(date_str, '%Y%m%d').date()
                    
                    if file_date < cutoff_date:
                        file_path.unlink()
                        logger.info(f"Deleted old file: {file_path}")
                        
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    continue

