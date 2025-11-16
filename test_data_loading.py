#!/usr/bin/env python3
"""
测试数据加载脚本
"""

import json
import os
from typing import Dict, Any

def load_platform_data(cache_dir: str, platform: str, keyword: str) -> Dict[str, Any]:
    """加载平台数据"""
    file_path = os.path.join(cache_dir, platform, f"{keyword}.json")
    if not os.path.exists(file_path):
        return {"status": "error", "posts": [], "error": f"File not found: {file_path}"}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"status": "error", "posts": [], "error": str(e)}

def test_data_loading():
    """测试数据加载"""
    cache_dir = "cache"
    platforms = ["hackernews", "reddit", "youtube", "discord"]
    keywords = ["ai", "iot", "mqtt", "unified_namespace"]
    
    print("🔍 Testing data loading...")
    print(f"Cache directory: {cache_dir}")
    print(f"Cache directory exists: {os.path.exists(cache_dir)}")
    
    if os.path.exists(cache_dir):
        print(f"Cache contents: {os.listdir(cache_dir)}")
    
    print("\n📊 Data loading results:")
    
    for keyword in keywords:
        print(f"\n🔑 Keyword: {keyword}")
        for platform in platforms:
            data = load_platform_data(cache_dir, platform, keyword)
            if data.get('status') == 'error':
                print(f"  ❌ {platform}: {data.get('error', 'No data found')}")
            else:
                posts = data.get('posts', [])
                metrics = data.get('metrics', {})
                print(f"  ✅ {platform}: {len(posts)} posts, metrics: {bool(metrics)}")

if __name__ == "__main__":
    test_data_loading()


