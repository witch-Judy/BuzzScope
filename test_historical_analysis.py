"""
测试历史数据分析功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 直接导入，避免相对导入问题
from src.services.historical_analysis_v2 import HistoricalAnalysisV2

def test_historical_analysis():
    """测试历史数据分析"""
    print("🧪 测试历史数据分析功能...")
    
    # 初始化分析服务
    analysis_service = HistoricalAnalysisV2()
    
    # 测试数据加载
    print("\n📊 测试数据加载...")
    for platform in ["reddit", "youtube", "discord"]:
        for keyword in ["ai", "iot"]:
            data = analysis_service.load_platform_data(platform, keyword)
            print(f"  {platform}/{keyword}: {data.get('total_posts', 0)} posts")
    
    # 测试指标计算
    print("\n📈 测试指标计算...")
    metrics = analysis_service.calculate_platform_metrics("reddit", "ai")
    print(f"  Reddit AI metrics:")
    print(f"    - Total posts: {metrics.total_posts}")
    print(f"    - Total interactions: {metrics.total_interactions}")
    print(f"    - Unique authors: {metrics.unique_authors}")
    print(f"    - Top contributors: {len(metrics.top_contributors)}")
    print(f"    - Top posts: {len(metrics.top_posts)}")
    
    # 测试关键词分析
    print("\n🔍 测试关键词分析...")
    keyword_results = analysis_service.analyze_keyword("ai")
    for platform, metrics in keyword_results.items():
        if metrics.total_posts > 0:
            print(f"  {platform}: {metrics.total_posts} posts, {metrics.total_interactions} interactions")
    
    # 测试对比分析
    print("\n🔄 测试对比分析...")
    comparison = analysis_service.compare_keywords(["ai", "iot"])
    print(f"  Keywords: {comparison.keywords}")
    print(f"  Platform totals: {comparison.platform_totals}")
    print(f"  Top keywords: {comparison.top_keywords}")
    print(f"  Insights: {len(comparison.cross_platform_insights)} insights")
    
    print("\n✅ 历史数据分析功能测试完成!")

if __name__ == "__main__":
    test_historical_analysis()
