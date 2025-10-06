#!/usr/bin/env python3
"""
Keyword Data Collection Script V2
Collects data for keywords with caching and historical data support
"""
import sys
import os
import argparse
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.data_collection_v2 import DataCollectionServiceV2

def main():
    parser = argparse.ArgumentParser(description='Collect keyword data with caching')
    parser.add_argument('keyword', help='Keyword to collect data for')
    parser.add_argument('--exact-match', action='store_true', 
                       help='Use exact phrase matching')
    parser.add_argument('--force-refresh', action='store_true',
                       help='Force refresh even if cached data exists')
    parser.add_argument('--output', help='Output file for results (JSON)')
    parser.add_argument('--format', choices=['json', 'summary'], default='summary',
                       help='Output format (default: summary)')
    parser.add_argument('--stats', action='store_true',
                       help='Show collection statistics')
    parser.add_argument('--clear-cache', action='store_true',
                       help='Clear cache for this keyword')
    
    args = parser.parse_args()
    
    print("📊 BuzzScope Keyword Data Collection V2")
    print("=" * 50)
    print(f"Keyword: {args.keyword}")
    print(f"Exact match: {args.exact_match}")
    print(f"Force refresh: {args.force_refresh}")
    
    # Initialize service
    service = DataCollectionServiceV2()
    
    # Handle special commands
    if args.stats:
        print("\n📈 Collection Statistics:")
        print("-" * 30)
        stats = service.get_collection_stats()
        
        print(f"Total cached keywords: {stats['total_cached_keywords']}")
        print("\nPlatform breakdown:")
        for platform, data in stats['platforms'].items():
            print(f"  {platform}: {data['cached_keywords']} keywords")
            if data['cache_files']:
                print(f"    Files: {', '.join(data['cache_files'][:3])}{'...' if len(data['cache_files']) > 3 else ''}")
        
        return
    
    if args.clear_cache:
        print(f"\n🗑️ Clearing cache for '{args.keyword}'...")
        service.clear_cache(args.keyword)
        print("✅ Cache cleared")
        return
    
    # Collect data
    print(f"\n🔄 Collecting data for '{args.keyword}'...")
    results = service.collect_keyword_data(
        keyword=args.keyword,
        exact_match=args.exact_match,
        force_refresh=args.force_refresh
    )
    
    # Display results
    if args.format == 'summary':
        print("\n📈 Collection Results:")
        print("-" * 30)
        
        for platform, data in results['platforms'].items():
            print(f"\n📱 {platform.upper()}:")
            
            if data['status'] == 'error':
                print(f"  ❌ Error: {data.get('error', 'Unknown error')}")
            elif data['status'] == 'cached':
                print(f"  💾 Using cached data")
                print(f"  📊 Total posts: {data.get('total_posts', 0)}")
                print(f"  📁 Data source: {data.get('data_source', 'unknown')}")
            else:
                print(f"  ✅ Status: {data['status']}")
                print(f"  📊 Total posts: {data.get('total_posts', 0)}")
                print(f"  📁 Data source: {data.get('data_source', 'unknown')}")
                print(f"  ⏰ Collected: {data.get('collection_time', 'unknown')}")
        
        # Summary
        total_posts = sum(
            data.get('total_posts', 0) 
            for data in results['platforms'].values() 
            if data['status'] != 'error'
        )
        successful_platforms = sum(
            1 for data in results['platforms'].values() 
            if data['status'] != 'error'
        )
        
        print(f"\n📊 Summary:")
        print(f"  Total posts found: {total_posts}")
        print(f"  Successful platforms: {successful_platforms}/{len(results['platforms'])}")
        
        # Show sample posts
        print(f"\n📝 Sample Posts:")
        for platform, data in results['platforms'].items():
            if data['status'] != 'error' and data.get('posts'):
                posts = data['posts'][:2]  # Show first 2 posts
                print(f"\n  {platform.upper()}:")
                for i, post in enumerate(posts, 1):
                    title = post.get('title', post.get('content', 'No title'))[:60]
                    print(f"    {i}. {title}...")
    
    elif args.format == 'json':
        print("\n📄 JSON Results:")
        print(json.dumps(results, indent=2, default=str))
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {args.output}")

if __name__ == "__main__":
    main()
