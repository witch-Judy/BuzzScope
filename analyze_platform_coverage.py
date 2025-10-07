#!/usr/bin/env python3
"""
Analyze platform data collection coverage and effectiveness
"""
import sys
import os
import json
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_collection_service import DataCollectionService
from src.collectors import HackerNewsCollector, RedditCollector, YouTubeCollector, DiscordCollector

def analyze_platform_coverage():
    """Analyze how well each platform is collecting data"""
    print("🔍 Analyzing Platform Data Collection Coverage")
    print("=" * 60)
    
    service = DataCollectionService()
    
    # Test with a common keyword
    test_keyword = "ai"
    days_back = 30
    
    print(f"📝 Test Keyword: {test_keyword}")
    print(f"📅 Time Range: {days_back} days back")
    print()
    
    # Analyze each platform
    platforms = {
        'hackernews': HackerNewsCollector(),
        'reddit': RedditCollector(),
        'youtube': YouTubeCollector(),
        'discord': DiscordCollector()
    }
    
    results = {}
    
    for platform_name, collector in platforms.items():
        print(f"📱 Analyzing {platform_name.upper()}...")
        
        try:
            # Test different collection methods
            if platform_name == 'hackernews':
                # Test comprehensive HN collection
                posts = collector.search_keyword(test_keyword, days_back, exact_match=False)
                
                # Test Show HN
                try:
                    show_posts = collector._get_show_hn_posts(limit=50)
                    show_filtered = collector.extract_keyword_mentions(show_posts, test_keyword, False)
                except:
                    show_filtered = []
                
                # Test Ask HN
                try:
                    ask_posts = collector._get_ask_hn_posts(limit=50)
                    ask_filtered = collector.extract_keyword_mentions(ask_posts, test_keyword, False)
                except:
                    ask_filtered = []
                
                results[platform_name] = {
                    'main_posts': len(posts),
                    'show_hn_posts': len(show_filtered),
                    'ask_hn_posts': len(ask_filtered),
                    'total_coverage': len(posts) + len(show_filtered) + len(ask_filtered),
                    'coverage_methods': ['top_stories', 'new_stories', 'best_stories', 'show_hn', 'ask_hn']
                }
                
            elif platform_name == 'reddit':
                # Test global vs subreddit search
                global_posts = collector.search_keyword(test_keyword, days_back, exact_match=False, use_global=True)
                
                # Test subreddit-only search
                subreddit_posts = collector.search_keyword(test_keyword, days_back, exact_match=False, use_global=False)
                
                results[platform_name] = {
                    'global_posts': len(global_posts),
                    'subreddit_posts': len(subreddit_posts),
                    'total_coverage': len(global_posts),
                    'coverage_methods': ['global_search', 'subreddit_search'],
                    'subreddits_covered': len(collector.subreddits)
                }
                
            elif platform_name == 'youtube':
                # Test YouTube search
                posts = collector.search_keyword(test_keyword, days_back, exact_match=False)
                
                # Test recent posts
                try:
                    recent_posts = collector.get_recent_posts(limit=50)
                    recent_filtered = collector.extract_keyword_mentions(recent_posts, test_keyword, False)
                except:
                    recent_filtered = []
                
                results[platform_name] = {
                    'search_posts': len(posts),
                    'recent_posts': len(recent_filtered),
                    'total_coverage': len(posts),
                    'coverage_methods': ['keyword_search', 'recent_videos'],
                    'max_results': collector.max_results
                }
                
            elif platform_name == 'discord':
                # Test Discord archive search
                posts = collector.search_keyword(test_keyword, days_back, exact_match=False)
                
                results[platform_name] = {
                    'archive_posts': len(posts),
                    'total_coverage': len(posts),
                    'coverage_methods': ['local_archives'],
                    'archive_files': len([f for f in os.listdir(collector.discord_raw_data_dir) if f.endswith(('.json', '.csv'))])
                }
            
            print(f"  ✅ {platform_name}: {results[platform_name]['total_coverage']} posts collected")
            
        except Exception as e:
            results[platform_name] = {
                'error': str(e),
                'total_coverage': 0
            }
            print(f"  ❌ {platform_name}: Error - {e}")
    
    # Print detailed analysis
    print(f"\n{'='*60}")
    print("📊 PLATFORM COVERAGE ANALYSIS")
    print(f"{'='*60}")
    
    for platform_name, data in results.items():
        print(f"\n📱 {platform_name.upper()}:")
        
        if 'error' in data:
            print(f"  ❌ Error: {data['error']}")
            continue
        
        print(f"  📊 Total Posts: {data['total_coverage']}")
        print(f"  🔧 Methods: {', '.join(data.get('coverage_methods', []))}")
        
        if platform_name == 'hackernews':
            print(f"  📝 Main Posts: {data['main_posts']}")
            print(f"  🎯 Show HN: {data['show_hn_posts']}")
            print(f"  ❓ Ask HN: {data['ask_hn_posts']}")
            
        elif platform_name == 'reddit':
            print(f"  🌐 Global Search: {data['global_posts']}")
            print(f"  🏘️ Subreddit Search: {data['subreddit_posts']}")
            print(f"  📍 Subreddits Covered: {data['subreddits_covered']}")
            
        elif platform_name == 'youtube':
            print(f"  🔍 Keyword Search: {data['search_posts']}")
            print(f"  📅 Recent Videos: {data['recent_posts']}")
            print(f"  📊 Max Results: {data['max_results']}")
            
        elif platform_name == 'discord':
            print(f"  📁 Archive Files: {data['archive_files']}")
    
    # Recommendations
    print(f"\n{'='*60}")
    print("💡 RECOMMENDATIONS FOR IMPROVEMENT")
    print(f"{'='*60}")
    
    for platform_name, data in results.items():
        if 'error' in data:
            continue
            
        print(f"\n📱 {platform_name.upper()}:")
        
        if platform_name == 'hackernews':
            if data['show_hn_posts'] == 0 and data['ask_hn_posts'] == 0:
                print("  💡 Consider expanding Show HN and Ask HN collection")
            if data['total_coverage'] < 10:
                print("  💡 Consider increasing collection limits or time range")
                
        elif platform_name == 'reddit':
            if data['global_posts'] < data['subreddit_posts']:
                print("  💡 Global search is less effective than subreddit search")
            if data['subreddits_covered'] < 10:
                print("  💡 Consider adding more tech-related subreddits")
                
        elif platform_name == 'youtube':
            if data['total_coverage'] < 20:
                print("  💡 Consider increasing max_results or using multiple search terms")
            if data['recent_posts'] == 0:
                print("  💡 Recent posts collection not working effectively")
                
        elif platform_name == 'discord':
            if data['archive_files'] == 0:
                print("  💡 No Discord archive files found - consider adding more")
            if data['total_coverage'] == 0:
                print("  💡 Discord archive search not finding relevant content")

def analyze_technical_voice_metrics():
    """Analyze if we're capturing technical voice metrics effectively"""
    print(f"\n{'='*60}")
    print("🎯 TECHNICAL VOICE ANALYSIS")
    print(f"{'='*60}")
    
    # Load some sample data
    service = DataCollectionService()
    
    # Check what metrics we're capturing
    test_keywords = ['ai', 'iot']
    
    for keyword in test_keywords:
        print(f"\n📝 Analyzing '{keyword}' for technical voice metrics:")
        
        try:
            # Get historical data
            status = service.get_keyword_status(keyword)
            if not status['has_historical_data']:
                print(f"  ❌ No historical data for '{keyword}'")
                continue
            
            # Load and analyze data
            from src.analyzers.historical_analyzer import HistoricalAnalyzer
            analyzer = HistoricalAnalyzer()
            analysis = analyzer.analyze_keyword_from_historical(keyword)
            
            if 'error' in analysis:
                print(f"  ❌ Analysis error: {analysis['error']}")
                continue
            
            for platform, data in analysis['platforms'].items():
                if 'error' in data:
                    continue
                    
                print(f"  📱 {platform.upper()}:")
                
                # Check key technical voice metrics
                metrics_to_check = [
                    'total_posts', 'unique_authors', 'total_score', 
                    'total_comments', 'total_views', 'total_likes'
                ]
                
                for metric in metrics_to_check:
                    value = data.get(metric, 0)
                    if value > 0:
                        print(f"    ✅ {metric}: {value}")
                    else:
                        print(f"    ❌ {metric}: {value}")
                
                # Check if we have engagement data
                if 'daily_activity' in data and data['daily_activity']:
                    print(f"    ✅ Daily activity trends: {len(data['daily_activity'])} data points")
                else:
                    print(f"    ❌ Daily activity trends: No data")
                
                # Check if we have top contributors
                if 'top_contributors' in data and data['top_contributors']:
                    print(f"    ✅ Top contributors: {len(data['top_contributors'])} identified")
                else:
                    print(f"    ❌ Top contributors: No data")
                
                # Check if we have sample posts
                if 'sample_posts' in data and data['sample_posts']:
                    print(f"    ✅ Sample posts: {len(data['sample_posts'])} available")
                else:
                    print(f"    ❌ Sample posts: No data")
        
        except Exception as e:
            print(f"  ❌ Error analyzing '{keyword}': {e}")

if __name__ == "__main__":
    analyze_platform_coverage()
    analyze_technical_voice_metrics()
