"""
Keyword management system for BuzzScope
"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from dataclasses import dataclass, asdict
import logging
from .config import Config

logger = logging.getLogger(__name__)

@dataclass
class KeywordConfig:
    """Configuration for a keyword"""
    keyword: str
    platforms: List[str]
    enabled: bool = True
    created_at: str = ""
    last_analyzed: str = ""
    analysis_frequency_days: int = 7
    custom_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.last_analyzed:
            self.last_analyzed = datetime.now().isoformat()
        if self.custom_settings is None:
            self.custom_settings = {}

class KeywordManager:
    """Manages keyword configurations and tracking"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.path.join(Config.DATA_DIR, 'keywords.json')
        self.keywords: Dict[str, KeywordConfig] = {}
        self.load_keywords()
    
    def add_keyword(self, keyword: str, platforms: List[str], 
                   analysis_frequency_days: int = 7,
                   custom_settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a new keyword to track
        
        Args:
            keyword: The keyword to track
            platforms: List of platforms to track on
            analysis_frequency_days: How often to analyze (in days)
            custom_settings: Custom settings for this keyword
            
        Returns:
            True if added successfully, False if already exists
        """
        if keyword in self.keywords:
            logger.warning(f"Keyword '{keyword}' already exists")
            return False
        
        # Validate platforms
        valid_platforms = [p for p in platforms if Config.is_platform_enabled(p)]
        if not valid_platforms:
            logger.error(f"No valid platforms for keyword '{keyword}'")
            return False
        
        keyword_config = KeywordConfig(
            keyword=keyword,
            platforms=valid_platforms,
            analysis_frequency_days=analysis_frequency_days,
            custom_settings=custom_settings or {}
        )
        
        self.keywords[keyword] = keyword_config
        self.save_keywords()
        
        logger.info(f"Added keyword '{keyword}' for platforms: {valid_platforms}")
        return True
    
    def remove_keyword(self, keyword: str) -> bool:
        """
        Remove a keyword from tracking
        
        Args:
            keyword: The keyword to remove
            
        Returns:
            True if removed successfully, False if not found
        """
        if keyword not in self.keywords:
            logger.warning(f"Keyword '{keyword}' not found")
            return False
        
        del self.keywords[keyword]
        self.save_keywords()
        
        logger.info(f"Removed keyword '{keyword}'")
        return True
    
    def update_keyword(self, keyword: str, **kwargs) -> bool:
        """
        Update keyword configuration
        
        Args:
            keyword: The keyword to update
            **kwargs: Fields to update
            
        Returns:
            True if updated successfully, False if not found
        """
        if keyword not in self.keywords:
            logger.warning(f"Keyword '{keyword}' not found")
            return False
        
        keyword_config = self.keywords[keyword]
        
        # Update allowed fields
        allowed_fields = ['platforms', 'enabled', 'analysis_frequency_days', 'custom_settings']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(keyword_config, field, value)
            else:
                logger.warning(f"Unknown field '{field}' for keyword update")
        
        self.save_keywords()
        logger.info(f"Updated keyword '{keyword}'")
        return True
    
    def get_keyword(self, keyword: str) -> Optional[KeywordConfig]:
        """Get keyword configuration"""
        return self.keywords.get(keyword)
    
    def get_all_keywords(self) -> Dict[str, KeywordConfig]:
        """Get all keyword configurations"""
        return self.keywords.copy()
    
    def get_enabled_keywords(self) -> Dict[str, KeywordConfig]:
        """Get only enabled keywords"""
        return {k: v for k, v in self.keywords.items() if v.enabled}
    
    def get_keywords_for_platform(self, platform: str) -> List[str]:
        """Get keywords that are tracked on a specific platform"""
        return [k for k, config in self.keywords.items() 
                if config.enabled and platform in config.platforms]
    
    def get_keywords_due_for_analysis(self) -> List[str]:
        """Get keywords that are due for analysis"""
        due_keywords = []
        now = datetime.now()
        
        for keyword, config in self.keywords.items():
            if not config.enabled:
                continue
            
            try:
                last_analyzed = datetime.fromisoformat(config.last_analyzed)
                days_since_analysis = (now - last_analyzed).days
                
                if days_since_analysis >= config.analysis_frequency_days:
                    due_keywords.append(keyword)
                    
            except (ValueError, TypeError):
                # If last_analyzed is invalid, consider it due
                due_keywords.append(keyword)
        
        return due_keywords
    
    def mark_keyword_analyzed(self, keyword: str) -> bool:
        """Mark a keyword as recently analyzed"""
        if keyword not in self.keywords:
            return False
        
        self.keywords[keyword].last_analyzed = datetime.now().isoformat()
        self.save_keywords()
        return True
    
    def get_keyword_stats(self) -> Dict[str, Any]:
        """Get statistics about tracked keywords"""
        total_keywords = len(self.keywords)
        enabled_keywords = len(self.get_enabled_keywords())
        
        platform_counts = {}
        for config in self.keywords.values():
            for platform in config.platforms:
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        due_for_analysis = len(self.get_keywords_due_for_analysis())
        
        return {
            'total_keywords': total_keywords,
            'enabled_keywords': enabled_keywords,
            'platform_counts': platform_counts,
            'due_for_analysis': due_for_analysis
        }
    
    def export_keywords(self, file_path: str) -> bool:
        """Export keywords to a JSON file"""
        try:
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'keywords': {k: asdict(v) for k, v in self.keywords.items()}
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported keywords to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting keywords: {e}")
            return False
    
    def import_keywords(self, file_path: str, merge: bool = True) -> bool:
        """
        Import keywords from a JSON file
        
        Args:
            file_path: Path to the JSON file
            merge: If True, merge with existing keywords. If False, replace all.
            
        Returns:
            True if imported successfully
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            imported_keywords = import_data.get('keywords', {})
            
            if not merge:
                self.keywords.clear()
            
            imported_count = 0
            for keyword, config_data in imported_keywords.items():
                try:
                    keyword_config = KeywordConfig(**config_data)
                    self.keywords[keyword] = keyword_config
                    imported_count += 1
                except Exception as e:
                    logger.error(f"Error importing keyword '{keyword}': {e}")
                    continue
            
            self.save_keywords()
            logger.info(f"Imported {imported_count} keywords from {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing keywords: {e}")
            return False
    
    def load_keywords(self):
        """Load keywords from configuration file"""
        if not os.path.exists(self.config_file):
            logger.info(f"Keywords file not found at {self.config_file}, starting with empty configuration")
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            keywords_data = data.get('keywords', {})
            
            for keyword, config_data in keywords_data.items():
                try:
                    keyword_config = KeywordConfig(**config_data)
                    self.keywords[keyword] = keyword_config
                except Exception as e:
                    logger.error(f"Error loading keyword '{keyword}': {e}")
                    continue
            
            logger.info(f"Loaded {len(self.keywords)} keywords from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error loading keywords from {self.config_file}: {e}")
            self.keywords = {}
    
    def save_keywords(self):
        """Save keywords to configuration file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            data = {
                'saved_at': datetime.now().isoformat(),
                'keywords': {k: asdict(v) for k, v in self.keywords.items()}
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved {len(self.keywords)} keywords to {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error saving keywords to {self.config_file}: {e}")
            raise

