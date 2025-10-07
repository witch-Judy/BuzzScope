"""
测试数据检查逻辑
"""

import os
import json

def test_keyword_status():
    """测试关键词状态检查"""
    print("🧪 测试关键词状态检查...")
    
    cache_dir = "data/cache"
    keywords = ["ai", "iot", "mqtt", "unified_namespace"]
    platforms = ["hackernews", "reddit", "youtube", "discord"]
    
    for keyword in keywords:
        print(f"\n📊 检查关键词: {keyword}")
        has_data = False
        
        for platform in platforms:
            platform_dir = os.path.join(cache_dir, platform)
            cache_file = os.path.join(platform_dir, f"{keyword}.json")
            
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        posts_count = data.get('total_posts', 0)
                        print(f"  ✅ {platform}: {posts_count} posts")
                        has_data = True
                except Exception as e:
                    print(f"  ❌ {platform}: 文件读取错误 - {e}")
            else:
                print(f"  ❌ {platform}: 文件不存在")
        
        print(f"  📋 总体状态: {'有数据' if has_data else '无数据'}")

if __name__ == "__main__":
    test_keyword_status()
