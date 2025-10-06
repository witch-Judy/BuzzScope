"""
Test script to verify BuzzScope setup
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from src.config import Config
        print("✅ Config module imported successfully")
        
        from src.models import BasePost, HackerNewsPost, RedditPost, YouTubePost, DiscordPost
        print("✅ Models imported successfully")
        
        from src.storage import BuzzScopeStorage
        print("✅ Storage module imported successfully")
        
        from src.analysis_v2 import BuzzScopeAnalyzerV2
        print("✅ Analysis module imported successfully")
        
        from src.keyword_manager import KeywordManager
        print("✅ Keyword manager imported successfully")
        
        from src.collectors import HackerNewsCollector, RedditCollector, YouTubeCollector, DiscordIncrementalCollector
        print("✅ Collectors imported successfully")
        
        from src.services import HistoricalAnalysisService, EventDrivenService
        print("✅ Services imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration"""
    try:
        from src.config import Config
        
        print(f"✅ Data directory: {Config.DATA_DIR}")
        print(f"✅ Platforms configured: {list(Config.PLATFORMS.keys())}")
        
        # Check platform status
        for platform, config in Config.PLATFORMS.items():
            status = "✅ Enabled" if Config.is_platform_enabled(platform) else "❌ Disabled"
            print(f"  {platform}: {status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_storage():
    """Test storage system"""
    try:
        from src.storage import BuzzScopeStorage
        
        storage = BuzzScopeStorage()
        print("✅ Storage system initialized")
        
        stats = storage.get_storage_stats()
        print(f"✅ Storage stats: {stats['total_posts']} posts across {stats['total_platforms']} platforms")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage error: {e}")
        return False

def test_keyword_manager():
    """Test keyword manager"""
    try:
        from src.keyword_manager import KeywordManager
        
        manager = KeywordManager()
        print("✅ Keyword manager initialized")
        
        stats = manager.get_keyword_stats()
        print(f"✅ Keyword stats: {stats['total_keywords']} keywords configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Keyword manager error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 BuzzScope Setup Test")
    print("=" * 30)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_config),
        ("Storage Test", test_storage),
        ("Keyword Manager Test", test_keyword_manager),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 20)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
    print("🎉 All tests passed! BuzzScope is ready to use.")
    print("\nNext steps:")
    print("1. Copy env.example to .env and add your API keys")
    print("2. Run: streamlit run app.py")
    print("3. Or run: python analyze_historical.py 'keyword' --exact-match")
    print("4. Or run: python monitor_keywords.py 'keyword' --once")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

