#!/usr/bin/env python3
"""
测试Hacker News的blockchain搜索
"""

import sys
import os
sys.path.append('.')

from src.collectors.hackernews_collector import HackerNewsCollector

def test_blockchain_search():
    print("🔍 Testing Hacker News blockchain search...")
    
    collector = HackerNewsCollector()
    
    # 测试精确匹配
    print("\n1. Testing exact match...")
    posts_exact = collector.search_keyword('blockchain', exact_match=True)
    print(f"Found {len(posts_exact)} posts with exact match")
    
    if posts_exact:
        print("Sample exact match posts:")
        for i, post in enumerate(posts_exact[:3]):
            print(f"  {i+1}. {post.title[:80]}...")
            print(f"     Author: {post.by}, Score: {post.score}")
    
    # 测试子字符串匹配
    print("\n2. Testing substring match...")
    posts_substring = collector.search_keyword('blockchain', exact_match=False)
    print(f"Found {len(posts_substring)} posts with substring match")
    
    if posts_substring:
        print("Sample substring match posts:")
        for i, post in enumerate(posts_substring[:3]):
            print(f"  {i+1}. {post.title[:80]}...")
            print(f"     Author: {post.by}, Score: {post.score}")
    
    # 测试其他相关关键词
    print("\n3. Testing related keywords...")
    related_keywords = ['crypto', 'bitcoin', 'ethereum', 'defi']
    
    for keyword in related_keywords:
        posts = collector.search_keyword(keyword, exact_match=False)
        print(f"  {keyword}: {len(posts)} posts")

if __name__ == "__main__":
    test_blockchain_search()


