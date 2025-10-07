"""
Discord data collector (for local JSON/HTML archives)
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .base_collector import BaseCollector
from ..models import DiscordPost
from ..config import Config

class DiscordCollector(BaseCollector):
    """Collector for Discord data from local archives"""
    
    def __init__(self):
        super().__init__("discord")
        self.data_format = Config.get_platform_config('discord').get('data_format', 'json')
        self.discord_data_dir = os.path.join(Config.DATA_DIR, 'discord_archives')
        
        # Ensure Discord data directory exists
        os.makedirs(self.discord_data_dir, exist_ok=True)
        
        if not Config.is_platform_enabled('discord'):
            self.logger.warning("Discord data collection not configured. Place JSON archives in ./data/discord_archives/")
    
    def search_keyword(self, keyword: str, days_back: int = 30, exact_match: bool = False) -> List[DiscordPost]:
        """Search Discord archives for keyword mentions"""
        self.logger.info(f"Searching Discord archives for keyword: {keyword} (exact_match={exact_match})")
        
        posts = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Search through all JSON files in the Discord data directory
        for filename in os.listdir(self.discord_data_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.discord_data_dir, filename)
                try:
                    file_posts = self._search_file(file_path, keyword, cutoff_date)
                    posts.extend(file_posts)
                except Exception as e:
                    self.logger.error(f"Error processing {filename}: {e}")
                    continue
        
        self.logger.info(f"Found {len(posts)} Discord messages mentioning '{keyword}'")
        return self.clean_posts(posts)
    
    def get_recent_posts(self, limit: int = 100) -> List[DiscordPost]:
        """Get recent posts from Discord archives"""
        self.logger.info(f"Getting {limit} recent posts from Discord archives")
        
        posts = []
        
        # Collect posts from all files
        for filename in os.listdir(self.discord_data_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.discord_data_dir, filename)
                try:
                    file_posts = self._get_recent_from_file(file_path, limit // 4)  # Distribute across files
                    posts.extend(file_posts)
                except Exception as e:
                    self.logger.error(f"Error processing {filename}: {e}")
                    continue
        
        # Sort by timestamp and return most recent
        posts.sort(key=lambda x: x.timestamp, reverse=True)
        return posts[:limit]
    
    def _search_file(self, file_path: str, keyword: str, cutoff_date: datetime) -> List[DiscordPost]:
        """Search a single Discord archive file for keyword mentions"""
        posts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different Discord export formats
            messages = self._extract_messages(data)
            
            for message in messages:
                # Check if message contains keyword
                if keyword.lower() in message.get('content', '').lower():
                    # Check if message is within date range
                    message_date = self._parse_discord_timestamp(message.get('timestamp'))
                    if message_date:
                        # Handle timezone-aware and timezone-naive timestamps
                        if message_date.tzinfo is not None:
                            message_date = message_date.replace(tzinfo=None)
                        
                        if message_date >= cutoff_date:
                            post = self._convert_message(message, file_path)
                            if post:
                                posts.append(post)
                            
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")
        
        return posts
    
    def _get_recent_from_file(self, file_path: str, limit: int) -> List[DiscordPost]:
        """Get recent messages from a single Discord archive file"""
        posts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = self._extract_messages(data)
            
            # Sort by timestamp and get most recent
            messages.sort(key=lambda x: self._parse_discord_timestamp(x.get('timestamp', '')), reverse=True)
            
            for message in messages[:limit]:
                post = self._convert_message(message, file_path)
                if post:
                    posts.append(post)
                    
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")
        
        return posts
    
    def _extract_messages(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract messages from Discord export data"""
        messages = []
        
        # Handle different export formats
        if 'messages' in data:
            # Standard DiscordChatExporter format
            messages = data['messages']
        elif isinstance(data, list):
            # Simple list of messages
            messages = data
        elif 'guild' in data and 'channels' in data:
            # Guild export format
            for channel in data.get('channels', []):
                messages.extend(channel.get('messages', []))
        
        return messages
    
    def _parse_discord_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse Discord timestamp string"""
        if not timestamp_str:
            return None
        
        try:
            # Handle different timestamp formats
            if 'T' in timestamp_str:
                # ISO format
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Unix timestamp
                return datetime.fromtimestamp(float(timestamp_str))
        except (ValueError, TypeError):
            return None
    
    def _convert_message(self, message: Dict[str, Any], file_path: str) -> DiscordPost:
        """Convert Discord message to DiscordPost"""
        try:
            # Extract basic message data
            content = message.get('content', '')
            author = message.get('author', {}).get('name', 'Unknown')
            message_id = message.get('id', '')
            timestamp = self._parse_discord_timestamp(message.get('timestamp', ''))
            
            if not timestamp:
                return None
            
            # Extract channel/guild info from file path or message data
            channel_id = message.get('channelId', '')
            guild_id = message.get('guildId', '')
            
            # Get message URL (if available)
            message_url = message.get('url', '')
            
            # Extract reactions
            reactions = {}
            for reaction in message.get('reactions', []):
                emoji = reaction.get('emoji', {}).get('name', 'unknown')
                count = reaction.get('count', 0)
                reactions[emoji] = count
            
            return DiscordPost(
                platform="discord",
                post_id=message_id,
                title="",  # Discord messages don't have titles
                content=content,
                author=author,
                timestamp=timestamp,
                url=message_url,
                channel_id=channel_id,
                guild_id=guild_id,
                message_type=message.get('type', 'default'),
                reactions=reactions if reactions else None,
                metadata={
                    'file_source': os.path.basename(file_path),
                    'attachments': message.get('attachments', []),
                    'embeds': message.get('embeds', []),
                    'mentions': message.get('mentions', []),
                    'pinned': message.get('pinned', False)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error converting Discord message: {e}")
            return None
    
    def add_archive_file(self, file_path: str) -> bool:
        """Add a new Discord archive file to the collection"""
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return False
            
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.discord_data_dir, filename)
            
            # Copy file to Discord data directory
            import shutil
            shutil.copy2(file_path, dest_path)
            
            self.logger.info(f"Added Discord archive: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding archive file: {e}")
            return False

