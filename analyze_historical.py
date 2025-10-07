#!/usr/bin/env python3
"""
Historical Analysis Script
Analyzes keywords using historical data
"""
import sys
import os
import argparse
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services import HistoricalAnalysisService

def main():
    parser = argparse.ArgumentParser(description='Analyze keywords using historical data')
    parser.add_argument('keyword', help='Keyword to analyze')
    parser.add_argument('--exact-match', action='store_true', 
                       help='Use exact phrase matching')
    parser.add_argument('--output', help='Output file for results (JSON)')
    parser.add_argument('--format', choices=['json', 'summary'], default='summary',
                       help='Output format (default: summary)')
    
    args = parser.parse_args()
    
    print("📊 BuzzScope Historical Analysis")
    print("=" * 50)
    print(f"Keyword: {args.keyword}")
    print(f"Exact match: {args.exact_match}")
    
    # Initialize service
    service = HistoricalAnalysisService()
    
    # Analyze keyword
    print("\\n🔄 Analyzing keyword...")
    results = service.analyze_keyword(args.keyword, args.exact_match)
    
    # Display results
    if args.format == 'summary':
        print("\\n📈 Analysis Results:")
        print("-" * 30)
        
        for platform, data in results['platforms'].items():
            print(f"\\n📱 {platform.upper()}:")
            
            if 'error' in data:
                print(f"  ❌ {data['error']}")
            else:
                print(f"  ✅ Status: {data['status']}")
                print(f"  📊 Total posts: {data['total_posts']}")
                print(f"  📁 Data source: {data['data_source']}")
                
                if 'date_range' in data and data['date_range']['start']:
                    print(f"  📅 Date range: {data['date_range']['start']} to {data['date_range']['end']}")
                
                if 'files_used' in data:
                    print(f"  📄 Files used: {data['files_used']}")
                
                if 'communities_searched' in data:
                    print(f"  🏘️ Communities: {data['communities_searched']}")
        
        # Summary
        total_posts = sum(
            data.get('total_posts', 0) 
            for data in results['platforms'].values() 
            if 'error' not in data
        )
        successful_platforms = sum(
            1 for data in results['platforms'].values() 
            if 'error' not in data
        )
        
        print(f"\\n📊 Summary:")
        print(f"  Total posts found: {total_posts}")
        print(f"  Successful platforms: {successful_platforms}/{len(results['platforms'])}")
    
    elif args.format == 'json':
        print("\\n📄 JSON Results:")
        print(json.dumps(results, indent=2, default=str))
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\\n💾 Results saved to: {args.output}")

if __name__ == "__main__":
    main()
