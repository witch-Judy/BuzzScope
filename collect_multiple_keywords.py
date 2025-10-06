#!/usr/bin/env python3
"""
Multiple Keywords Data Collection Script
Collects data for multiple keywords with caching
"""
import sys
import os
import argparse
import json
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.data_collection_v2 import DataCollectionServiceV2

def main():
    parser = argparse.ArgumentParser(description='Collect data for multiple keywords')
    parser.add_argument('keywords', nargs='+', help='Keywords to collect data for')
    parser.add_argument('--exact-match', action='store_true', 
                       help='Use exact phrase matching')
    parser.add_argument('--force-refresh', action='store_true',
                       help='Force refresh even if cached data exists')
    parser.add_argument('--delay', type=int, default=2,
                       help='Delay between keyword collections in seconds (default: 2)')
    parser.add_argument('--output', help='Output file for results (JSON)')
    parser.add_argument('--format', choices=['json', 'summary'], default='summary',
                       help='Output format (default: summary)')
    
    args = parser.parse_args()
    
    print("📊 BuzzScope Multiple Keywords Data Collection")
    print("=" * 60)
    print(f"Keywords: {', '.join(args.keywords)}")
    print(f"Exact match: {args.exact_match}")
    print(f"Force refresh: {args.force_refresh}")
    print(f"Delay between collections: {args.delay}s")
    
    # Initialize service
    service = DataCollectionServiceV2()
    
    # Collect data for each keyword
    all_results = {}
    start_time = time.time()
    
    for i, keyword in enumerate(args.keywords, 1):
        print(f"\n🔄 [{i}/{len(args.keywords)}] Collecting data for '{keyword}'...")
        
        try:
            results = service.collect_keyword_data(
                keyword=keyword,
                exact_match=args.exact_match,
                force_refresh=args.force_refresh
            )
            all_results[keyword] = results
            
            # Show quick summary
            total_posts = sum(
                data.get('total_posts', 0) 
                for data in results['platforms'].values() 
                if data['status'] != 'error'
            )
            successful_platforms = sum(
                1 for data in results['platforms'].values() 
                if data['status'] != 'error'
            )
            
            print(f"  ✅ {total_posts} posts from {successful_platforms} platforms")
            
        except Exception as e:
            print(f"  ❌ Error collecting data for '{keyword}': {e}")
            all_results[keyword] = {'error': str(e)}
        
        # Delay between collections (except for last one)
        if i < len(args.keywords):
            time.sleep(args.delay)
    
    # Calculate total time
    total_time = time.time() - start_time
    
    # Display results
    if args.format == 'summary':
        print(f"\n📈 Collection Summary:")
        print("=" * 60)
        print(f"Total time: {total_time:.1f} seconds")
        print(f"Average time per keyword: {total_time/len(args.keywords):.1f} seconds")
        
        # Platform breakdown
        platform_totals = {}
        for keyword, results in all_results.items():
            if 'error' not in results:
                for platform, data in results['platforms'].items():
                    if data['status'] != 'error':
                        if platform not in platform_totals:
                            platform_totals[platform] = 0
                        platform_totals[platform] += data.get('total_posts', 0)
        
        print(f"\n📊 Platform Totals:")
        for platform, total in platform_totals.items():
            print(f"  {platform}: {total} posts")
        
        # Keyword breakdown
        print(f"\n🔍 Keyword Breakdown:")
        for keyword, results in all_results.items():
            if 'error' in results:
                print(f"  {keyword}: ❌ Error - {results['error']}")
            else:
                total_posts = sum(
                    data.get('total_posts', 0) 
                    for data in results['platforms'].values() 
                    if data['status'] != 'error'
                )
                successful_platforms = sum(
                    1 for data in results['platforms'].values() 
                    if data['status'] != 'error'
                )
                print(f"  {keyword}: {total_posts} posts from {successful_platforms} platforms")
    
    elif args.format == 'json':
        print("\n📄 JSON Results:")
        print(json.dumps(all_results, indent=2, default=str))
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {args.output}")
    
    # Show cache statistics
    print(f"\n💾 Cache Statistics:")
    stats = service.get_collection_stats()
    print(f"  Total cached keywords: {stats['total_cached_keywords']}")
    for platform, data in stats['platforms'].items():
        print(f"  {platform}: {data['cached_keywords']} keywords")

if __name__ == "__main__":
    main()
