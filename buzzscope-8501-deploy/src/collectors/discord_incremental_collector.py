"""
Discord Incremental Data Collector
Collects only new data since last collection for Discord
"""
import json
import os
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base_collector import BaseCollector
from ..models import DiscordPost
from ..config import Config

class DiscordIncrementalCollector(BaseCollector):
    """Incremental collector for Discord data"""
    
    def __init__(self):
        super().__init__("discord_incremental")
        self.discord_raw_data_dir = os.path.join(Config.DATA_DIR, 'discord_raw')
        self.discord_processed_dir = os.path.join(Config.DATA_DIR, 'discord')
        self.last_collection_file = os.path.join(Config.DATA_DIR, 'discord_last_collection.json')
        
        # Ensure directories exist
        os.makedirs(self.discord_processed_dir, exist_ok=True)
        os.makedirs(self.discord_raw_data_dir, exist_ok=True)
    
    def get_last_collection_time(self) -> datetime:
        """Get the timestamp of the last collection"""
        if os.path.exists(self.last_collection_file):
            try:
                with open(self.last_collection_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data['last_collection'])
            except:
                pass
        
        # Default to 7 days ago if no previous collection
        return datetime.now() - timedelta(days=7)
    
    def update_last_collection_time(self, timestamp: datetime = None):
        """Update the last collection timestamp"""
        if timestamp is None:
            timestamp = datetime.now()
        
        with open(self.last_collection_file, 'w') as f:
            json.dump({
                'last_collection': timestamp.isoformat(),
                'updated_at': datetime.now().isoformat()
            }, f, indent=2)
    
    def collect_new_data(self, days_back: int = 1) -> List[DiscordPost]:
        """Collect new Discord data since last collection"""
        self.logger.info(f"Collecting new Discord data for the last {days_back} days")
        
        last_collection = self.get_last_collection_time()
        new_posts = []
        
        # Process CSV files (DiscordChatExporter format)
        for root, _, files in os.walk(self.discord_raw_data_dir):
            for filename in files:
                if filename.endswith('.csv'):
                    file_path = os.path.join(root, filename)
                    try:
                        file_posts = self._process_csv_file(file_path, last_collection)
                        new_posts.extend(file_posts)
                    except Exception as e:
                        self.logger.error(f"Error processing CSV {file_path}: {e}")
                        continue
        
        # Process JSON files if any
        for root, _, files in os.walk(self.discord_raw_data_dir):
            for filename in files:
                if filename.endswith('.json'):
                    file_path = os.path.join(root, filename)
                    try:
                        file_posts = self._process_json_file(file_path, last_collection)
                        new_posts.extend(file_posts)
                    except Exception as e:
                        self.logger.error(f"Error processing JSON {file_path}: {e}")
                        continue
        
        self.logger.info(f"Found {len(new_posts)} new Discord messages")
        
        # Update last collection time
        if new_posts:
            self.update_last_collection_time()
        
        return self.clean_posts(new_posts)
    
    def _process_csv_file(self, file_path: str, since: datetime) -> List[DiscordPost]:
        """Process a CSV file and extract new messages"""
        new_posts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Parse timestamp
                    timestamp = self._parse_discord_timestamp(row.get('Date', ''))
                    if not timestamp or timestamp <= since:
                        continue
                    
                    # Convert to DiscordPost
                    post = self._convert_csv_row(row, file_path)
                    if post:
                        new_posts.append(post)
        
        except Exception as e:
            self.logger.error(f"Error reading CSV file {file_path}: {e}")
        
        return new_posts
    
    def _process_json_file(self, file_path: str, since: datetime) -> List[DiscordPost]:
        """Process a JSON file and extract new messages"""
        new_posts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle different JSON structures
                messages = []
                if isinstance(data, list):
                    messages = data
                elif isinstance(data, dict):
                    if 'messages' in data:
                        messages = data['messages']
                    elif 'data' in data:
                        messages = data['data']
                
                for message in messages:
                    # Parse timestamp
                    timestamp = self._parse_discord_timestamp(message.get('timestamp', ''))
                    if not timestamp or timestamp <= since:
                        continue
                    
                    # Convert to DiscordPost
                    post = self._convert_json_message(message, file_path)
                    if post:
                        new_posts.append(post)
        
        except Exception as e:
            self.logger.error(f"Error reading JSON file {file_path}: {e}")
        
        return new_posts
    
    def _parse_discord_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse Discord timestamp from various formats"""
        if not timestamp_str:
            return None
        
        try:
            # Handle 7-digit microseconds by truncating to 6 digits
            if '.0000000' in timestamp_str:
                timestamp_str = timestamp_str.replace('.0000000', '.000000')
            elif timestamp_str.count('.') == 1 and len(timestamp_str.split('.')[1]) > 6:
                # Truncate microseconds to 6 digits
                parts = timestamp_str.split('.')
                if len(parts[1]) > 6:
                    parts[1] = parts[1][:6]
                    timestamp_str = '.'.join(parts)
            
            # Handle different timestamp formats
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%fZ',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # Try ISO format with timezone handling
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            elif '+' in timestamp_str or timestamp_str.count('-') > 2:
                # Has timezone info
                return datetime.fromisoformat(timestamp_str)
            else:
                # No timezone info, treat as naive
                return datetime.fromisoformat(timestamp_str)
        
        except Exception as e:
            self.logger.warning(f"Could not parse timestamp '{timestamp_str}': {e}")
            return None
    
    def _convert_csv_row(self, row: Dict[str, str], file_path: str) -> Optional[DiscordPost]:
        """Convert CSV row to DiscordPost"""
        try:
            # Extract channel name from file path
            channel_name = os.path.basename(os.path.dirname(file_path))
            
            # Parse timestamp
            timestamp = self._parse_discord_timestamp(row.get('Date', ''))
            if not timestamp:
                return None
            
            # Extract author
            author = row.get('Author', '').strip()
            if not author:
                return None
            
            # Extract content
            content = row.get('Content', '').strip()
            if not content:
                return None
            
            # Extract reactions
            reactions = []
            if 'Reactions' in row and row['Reactions']:
                try:
                    reactions_data = json.loads(row['Reactions'])
                    reactions = reactions_data
                except:
                    pass
            
            return DiscordPost(
                post_id=f"discord_{hash(content + str(timestamp))}",
                title=f"Discord message in {channel_name}",
                content=content,
                author=author,
                timestamp=timestamp,
                url=f"discord://{channel_name}",
                score=len(reactions),
                platform="discord",
                channel=channel_name,
                reactions=reactions,
                attachments=row.get('Attachments', ''),
                mentions=row.get('Mentions', '')
            )
        
        except Exception as e:
            self.logger.error(f"Error converting CSV row: {e}")
            return None
    
    def _convert_json_message(self, message: Dict[str, Any], file_path: str) -> Optional[DiscordPost]:
        """Convert JSON message to DiscordPost"""
        try:
            # Extract channel name from file path
            channel_name = os.path.basename(os.path.dirname(file_path))
            
            # Parse timestamp
            timestamp = self._parse_discord_timestamp(message.get('timestamp', ''))
            if not timestamp:
                return None
            
            # Extract author
            author = message.get('author', {}).get('name', '') if isinstance(message.get('author'), dict) else str(message.get('author', ''))
            if not author:
                return None
            
            # Extract content
            content = message.get('content', '').strip()
            if not content:
                return None
            
            # Extract reactions
            reactions = message.get('reactions', [])
            
            return DiscordPost(
                post_id=f"discord_{message.get('id', hash(content + str(timestamp)))}",
                title=f"Discord message in {channel_name}",
                content=content,
                author=author,
                timestamp=timestamp,
                url=f"discord://{channel_name}",
                score=len(reactions),
                platform="discord",
                channel=channel_name,
                reactions=reactions,
                attachments=message.get('attachments', []),
                mentions=message.get('mentions', [])
            )
        
        except Exception as e:
            self.logger.error(f"Error converting JSON message: {e}")
            return None
    
    def search_keyword(self, keyword: str, days_back: int = 30, exact_match: bool = False) -> List[DiscordPost]:
        """Search through all collected Discord data (historical + new)"""
        self.logger.info(f"Searching Discord data for keyword: {keyword} (exact_match={exact_match})")
        
        # First collect any new data
        new_posts = self.collect_new_data(days_back=1)
        
        # Then search through all data (including historical)
        all_posts = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Search through processed data
        for root, _, files in os.walk(self.discord_processed_dir):
            for filename in files:
                if filename.endswith('.parquet'):
                    # This would require loading from parquet files
                    # For now, we'll rely on the raw data search
                    continue
        
        # Search through raw data
        for root, _, files in os.walk(self.discord_raw_data_dir):
            for filename in files:
                if filename.endswith('.csv'):
                    file_path = os.path.join(root, filename)
                    try:
                        file_posts = self._search_csv_file(file_path, keyword, cutoff_date, exact_match)
                        all_posts.extend(file_posts)
                    except Exception as e:
                        self.logger.error(f"Error searching CSV {file_path}: {e}")
                        continue
                elif filename.endswith('.json'):
                    file_path = os.path.join(root, filename)
                    try:
                        file_posts = self._search_json_file(file_path, keyword, cutoff_date, exact_match)
                        all_posts.extend(file_posts)
                    except Exception as e:
                        self.logger.error(f"Error searching JSON {file_path}: {e}")
                        continue
        
        # Add new posts
        new_filtered = self.extract_keyword_mentions(new_posts, keyword, exact_match)
        all_posts.extend(new_filtered)
        
        self.logger.info(f"Found {len(all_posts)} Discord messages mentioning '{keyword}'")
        return self.clean_posts(all_posts)
    
    def _search_csv_file(self, file_path: str, keyword: str, cutoff_date: datetime, exact_match: bool) -> List[DiscordPost]:
        """Search a CSV file for keyword mentions"""
        posts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Parse timestamp
                    timestamp = self._parse_discord_timestamp(row.get('Date', ''))
                    if not timestamp or timestamp < cutoff_date:
                        continue
                    
                    # Check if content contains keyword (or return all if no keyword)
                    content = row.get('Content', '')
                    if not keyword or self._contains_keyword(content, keyword, exact_match):
                        post = self._convert_csv_row(row, file_path)
                        if post:
                            posts.append(post)
        
        except Exception as e:
            self.logger.error(f"Error searching CSV file {file_path}: {e}")
        
        return posts
    
    def _search_json_file(self, file_path: str, keyword: str, cutoff_date: datetime, exact_match: bool) -> List[DiscordPost]:
        """Search a JSON file for keyword mentions"""
        posts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Handle different JSON structures
                messages = []
                if isinstance(data, list):
                    messages = data
                elif isinstance(data, dict):
                    if 'messages' in data:
                        messages = data['messages']
                    elif 'data' in data:
                        messages = data['data']
                
                for message in messages:
                    # Parse timestamp
                    timestamp = self._parse_discord_timestamp(message.get('timestamp', ''))
                    if not timestamp or timestamp < cutoff_date:
                        continue
                    
                    # Check if content contains keyword (or return all if no keyword)
                    content = message.get('content', '')
                    if not keyword or self._contains_keyword(content, keyword, exact_match):
                        post = self._convert_json_message(message, file_path)
                        if post:
                            posts.append(post)
        
        except Exception as e:
            self.logger.error(f"Error searching JSON file {file_path}: {e}")
        
        return posts
    
    def _contains_keyword(self, content: str, keyword: str, exact_match: bool) -> bool:
        """Check if content contains keyword"""
        if not content or not keyword:
            return False
        
        if exact_match:
            return keyword.lower() in content.lower()
        else:
            # Split keyword into words and check if all words are present
            keyword_words = keyword.lower().split()
            content_lower = content.lower()
            return all(word in content_lower for word in keyword_words)
    
    def get_recent_posts(self, limit: int = 100) -> List[DiscordPost]:
        """Get recent posts from Discord data"""
        self.logger.info(f"Getting {limit} recent posts from Discord data")
        
        all_posts = []
        cutoff_date = datetime.now() - timedelta(days=7)  # Last 7 days
        
        # Search through Discord data directory
        for root, _, files in os.walk(self.discord_processed_dir):
            for filename in files:
                if filename.endswith('.csv'):
                    file_path = os.path.join(root, filename)
                    try:
                        file_posts = self._search_csv_file(file_path, "", cutoff_date, False)  # Empty keyword to get all
                        all_posts.extend(file_posts)
                    except Exception as e:
                        self.logger.error(f"Error getting recent posts from CSV {file_path}: {e}")
                        continue
                elif filename.endswith('.json'):
                    file_path = os.path.join(root, filename)
                    try:
                        file_posts = self._search_json_file(file_path, "", cutoff_date, False)  # Empty keyword to get all
                        all_posts.extend(file_posts)
                    except Exception as e:
                        self.logger.error(f"Error getting recent posts from JSON {file_path}: {e}")
                        continue
        
        # Sort by timestamp and return most recent
        all_posts.sort(key=lambda x: x.timestamp, reverse=True)
        return all_posts[:limit]