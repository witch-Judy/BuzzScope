"""
Main runner script for BuzzScope
"""
import sys
import os
import argparse
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.storage import BuzzScopeStorage
from src.analysis import BuzzScopeAnalyzer
from src.keyword_manager import KeywordManager
from src.collectors import (
    HackerNewsCollector, RedditCollector, 
    YouTubeCollector, DiscordCollector
)

def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('buzzscope.log')
        ]
    )

def collect_data(keyword: str, platforms: list, days_back: int = 30):
    """Collect data for a keyword from specified platforms"""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting data collection for keyword: {keyword}")
    
    # Initialize components
    storage = BuzzScopeStorage()
    collectors = {
        'hackernews': HackerNewsCollector(),
        'reddit': RedditCollector(),
        'youtube': YouTubeCollector(),
        'discord': DiscordCollector()
    }
    
    total_posts = 0
    
    for platform in platforms:
        if platform not in collectors:
            logger.warning(f"Unknown platform: {platform}")
            continue
        
        if not Config.is_platform_enabled(platform):
            logger.warning(f"Platform {platform} is not enabled or configured")
            continue
        
        logger.info(f"Collecting data from {platform}...")
        
        try:
            collector = collectors[platform]
            posts = collector.search_keyword(keyword, days_back)
            
            if posts:
                storage.save_posts(posts, platform)
                total_posts += len(posts)
                logger.info(f"Collected {len(posts)} posts from {platform}")
            else:
                logger.info(f"No posts found for '{keyword}' in {platform}")
                
        except Exception as e:
            logger.error(f"Error collecting from {platform}: {e}")
            continue
    
    logger.info(f"Data collection complete. Total posts collected: {total_posts}")
    return total_posts

def analyze_keyword(keyword: str, platforms: list = None, days_back: int = 30):
    """Analyze a keyword across platforms"""
    logger = logging.getLogger(__name__)
    logger.info(f"Starting analysis for keyword: {keyword}")
    
    # Initialize components
    analyzer = BuzzScopeAnalyzer()
    
    if platforms is None:
        platforms = list(Config.PLATFORMS.keys())
    
    # Perform analysis
    results = analyzer.analyze_keyword(keyword, platforms, days_back)
    
    if not results:
        logger.warning(f"No data found for keyword '{keyword}'")
        return
    
    # Print results
    print(f"\n📊 Analysis Results for '{keyword}'")
    print("=" * 50)
    
    total_mentions = sum(metrics.total_mentions for metrics in results.values())
    total_authors = sum(metrics.unique_authors for metrics in results.values())
    total_interactions = sum(metrics.total_interactions for metrics in results.values())
    
    print(f"Total Mentions: {total_mentions}")
    print(f"Unique Authors: {total_authors}")
    print(f"Total Interactions: {total_interactions:,}")
    print(f"Active Platforms: {len(results)}")
    
    for platform, metrics in results.items():
        print(f"\n🌐 {platform.title()}:")
        print(f"  Mentions: {metrics.total_mentions}")
        print(f"  Authors: {metrics.unique_authors}")
        print(f"  Interactions: {metrics.total_interactions:,}")
        
        if metrics.top_contributors:
            print(f"  Top Contributors:")
            for contributor in metrics.top_contributors[:3]:
                print(f"    • {contributor['author']}: {contributor['post_count']} posts")

def manage_keywords():
    """Interactive keyword management"""
    keyword_manager = KeywordManager()
    
    while True:
        print("\n🔧 Keyword Management")
        print("1. List keywords")
        print("2. Add keyword")
        print("3. Remove keyword")
        print("4. Update keyword")
        print("5. Show statistics")
        print("6. Export keywords")
        print("7. Import keywords")
        print("0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            keywords = keyword_manager.get_all_keywords()
            if keywords:
                print("\n📋 Tracked Keywords:")
                for keyword, config in keywords.items():
                    status = "✅" if config.enabled else "❌"
                    print(f"  {status} {keyword} - Platforms: {', '.join(config.platforms)}")
            else:
                print("No keywords configured")
        
        elif choice == "2":
            keyword = input("Enter keyword: ").strip()
            if not keyword:
                print("Invalid keyword")
                continue
            
            print("Available platforms:", list(Config.PLATFORMS.keys()))
            platforms_input = input("Enter platforms (comma-separated): ").strip()
            platforms = [p.strip() for p in platforms_input.split(',') if p.strip()]
            
            if keyword_manager.add_keyword(keyword, platforms):
                print(f"✅ Added keyword '{keyword}'")
            else:
                print(f"❌ Failed to add keyword '{keyword}'")
        
        elif choice == "3":
            keyword = input("Enter keyword to remove: ").strip()
            if keyword_manager.remove_keyword(keyword):
                print(f"✅ Removed keyword '{keyword}'")
            else:
                print(f"❌ Keyword '{keyword}' not found")
        
        elif choice == "4":
            keyword = input("Enter keyword to update: ").strip()
            if keyword not in keyword_manager.get_all_keywords():
                print(f"❌ Keyword '{keyword}' not found")
                continue
            
            print("1. Toggle enabled/disabled")
            print("2. Update platforms")
            print("3. Update analysis frequency")
            
            update_choice = input("Select update type: ").strip()
            
            if update_choice == "1":
                current_config = keyword_manager.get_keyword(keyword)
                new_status = not current_config.enabled
                keyword_manager.update_keyword(keyword, enabled=new_status)
                print(f"✅ Updated keyword '{keyword}' enabled status to {new_status}")
            
            elif update_choice == "2":
                print("Available platforms:", list(Config.PLATFORMS.keys()))
                platforms_input = input("Enter new platforms (comma-separated): ").strip()
                platforms = [p.strip() for p in platforms_input.split(',') if p.strip()]
                keyword_manager.update_keyword(keyword, platforms=platforms)
                print(f"✅ Updated platforms for keyword '{keyword}'")
            
            elif update_choice == "3":
                frequency = input("Enter analysis frequency (days): ").strip()
                try:
                    frequency = int(frequency)
                    keyword_manager.update_keyword(keyword, analysis_frequency_days=frequency)
                    print(f"✅ Updated analysis frequency for keyword '{keyword}'")
                except ValueError:
                    print("❌ Invalid frequency")
        
        elif choice == "5":
            stats = keyword_manager.get_keyword_stats()
            print(f"\n📊 Keyword Statistics:")
            print(f"  Total Keywords: {stats['total_keywords']}")
            print(f"  Enabled Keywords: {stats['enabled_keywords']}")
            print(f"  Due for Analysis: {stats['due_for_analysis']}")
            print(f"  Platform Distribution:")
            for platform, count in stats['platform_counts'].items():
                print(f"    {platform}: {count} keywords")
        
        elif choice == "6":
            filename = input("Enter export filename (default: keywords_export.json): ").strip()
            if not filename:
                filename = "keywords_export.json"
            
            if keyword_manager.export_keywords(filename):
                print(f"✅ Exported keywords to {filename}")
            else:
                print("❌ Export failed")
        
        elif choice == "7":
            filename = input("Enter import filename: ").strip()
            if not os.path.exists(filename):
                print(f"❌ File {filename} not found")
                continue
            
            merge = input("Merge with existing keywords? (y/n): ").strip().lower() == 'y'
            
            if keyword_manager.import_keywords(filename, merge=merge):
                print(f"✅ Imported keywords from {filename}")
            else:
                print("❌ Import failed")
        
        elif choice == "0":
            break
        
        else:
            print("❌ Invalid option")

def show_storage_stats():
    """Show storage statistics"""
    storage = BuzzScopeStorage()
    stats = storage.get_storage_stats()
    
    print("\n📊 Storage Statistics")
    print("=" * 30)
    print(f"Total Platforms: {stats['total_platforms']}")
    print(f"Total Posts: {stats['total_posts']:,}")
    
    if stats['date_range']:
        print(f"Date Range: {stats['date_range'][0]} to {stats['date_range'][1]}")
    
    if stats['platform_stats']:
        print("\nPlatform Details:")
        for platform, data in stats['platform_stats'].items():
            print(f"  {platform.title()}: {data['total_posts']} posts, {data['files']} files")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="BuzzScope - Keyword Tracking Tool")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set logging level")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Collect command
    collect_parser = subparsers.add_parser("collect", help="Collect data for a keyword")
    collect_parser.add_argument("keyword", help="Keyword to collect data for")
    collect_parser.add_argument("--platforms", nargs="+", 
                               choices=list(Config.PLATFORMS.keys()),
                               default=list(Config.PLATFORMS.keys()),
                               help="Platforms to collect from")
    collect_parser.add_argument("--days", type=int, default=30,
                               help="Days to look back")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a keyword")
    analyze_parser.add_argument("keyword", help="Keyword to analyze")
    analyze_parser.add_argument("--platforms", nargs="+",
                               choices=list(Config.PLATFORMS.keys()),
                               help="Platforms to analyze (default: all)")
    analyze_parser.add_argument("--days", type=int, default=30,
                               help="Days to look back")
    
    # Keywords command
    subparsers.add_parser("keywords", help="Manage keywords")
    
    # Stats command
    subparsers.add_parser("stats", help="Show storage statistics")
    
    # Streamlit command
    subparsers.add_parser("app", help="Launch Streamlit application")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    if args.command == "collect":
        collect_data(args.keyword, args.platforms, args.days)
    
    elif args.command == "analyze":
        analyze_keyword(args.keyword, args.platforms, args.days)
    
    elif args.command == "keywords":
        manage_keywords()
    
    elif args.command == "stats":
        show_storage_stats()
    
    elif args.command == "app":
        import subprocess
        subprocess.run(["streamlit", "run", "app.py"])
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

