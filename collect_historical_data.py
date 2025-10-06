#!/usr/bin/env python3
"""
Script to collect historical data for testing keywords
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.collectors.historical_collector import HistoricalCollector
from datetime import datetime

def main():
    print("🚀 Starting Historical Data Collection")
    print("=" * 50)
    
    # Initialize collector
    collector = HistoricalCollector()
    
    # Define test keywords
    test_keywords = ['unified namespace', 'iot', 'mqtt', 'ai']
    
    print(f"📝 Test Keywords: {test_keywords}")
    print(f"⏰ Collection Time: {datetime.now()}")
    print()
    
    # Set time range (default to 30 days for testing)
    days_back = 30
    print(f"Using {days_back} days for historical data collection (default for testing)")
    
    print(f"\n📊 Collecting {days_back} days of historical data")
    print("⚠️  This may take a while due to API rate limits...")
    print()
    
    # Start collection
    try:
        results = collector.build_keyword_database(test_keywords, days_back)
        
        print("\n✅ Collection Complete!")
        print("=" * 50)
        
        # Print summary
        for keyword, platforms in results.items():
            print(f"\n📋 {keyword.upper()}:")
            for platform, result in platforms.items():
                if 'error' in result:
                    print(f"  ❌ {platform}: {result['error']}")
                else:
                    if platform == 'youtube':
                        count = result.get('videos_collected', 0)
                    else:
                        count = result.get('posts_collected', 0)
                    print(f"  ✅ {platform}: {count} items")
        
        print(f"\n📁 Data saved to: ./data/historical/")
        print("🎯 You can now use this data for testing!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Collection interrupted by user")
    except Exception as e:
        print(f"\n❌ Collection failed: {e}")

if __name__ == "__main__":
    main()
