#!/bin/bash

# BuzzScope Historical Analysis - 快速部署脚本
echo "🚀 BuzzScope Historical Analysis - Quick Deploy to GitHub..."

# 检查是否在正确的目录
if [ ! -f "app_simple_historical.py" ]; then
    echo "❌ Please run this script from the buzzscope-8501-deploy directory"
    exit 1
fi

# 检查缓存数据
if [ ! -d "cache" ]; then
    echo "❌ Cache directory not found"
    exit 1
fi

echo "📊 Cache data size: $(du -sh cache/ | cut -f1)"
echo "📁 Total package size: $(du -sh . | cut -f1)"

# 初始化git仓库
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
    git branch -M main
fi

# 添加文件
echo "📋 Adding files to git..."
git add .

# 提交
echo "💾 Committing changes..."
git commit -m "BuzzScope Historical Analysis - Technology Trend Dashboard

- Multi-platform analysis (Hacker News, Reddit, YouTube, Discord)
- Pre-cached historical data for fast loading
- Support for keywords: ai, iot, mqtt, unified_namespace
- Interactive charts and trend analysis
- Cross-platform comparison features"

echo "✅ Ready for GitHub push!"
echo ""
echo "📋 Next steps:"
echo "1. Create a new repository on GitHub:"
echo "   - Name: buzzscope-historical (or your preferred name)"
echo "   - Description: BuzzScope Historical Analysis - Technology Trend Dashboard"
echo "   - Set as PUBLIC repository"
echo "   - Don't initialize with README (we already have one)"
echo ""
echo "2. Connect to GitHub:"
echo "   git remote add origin https://github.com/yourusername/buzzscope-historical.git"
echo "   git push -u origin main"
echo ""
echo "3. Deploy to Streamlit Cloud:"
echo "   - Go to https://share.streamlit.io"
echo "   - Click 'New app'"
echo "   - Connect GitHub account"
echo "   - Select repository: buzzscope-historical"
echo "   - Main file: app_simple_historical.py"
echo "   - App URL: buzzscope-historical (or custom)"
echo "   - Click 'Deploy!'"
echo ""
echo "🌐 Your app will be available at: https://buzzscope-historical.streamlit.app"
echo ""
echo "🎯 Features:"
echo "✅ No API keys required"
echo "✅ Fast loading with pre-cached data"
echo "✅ Public access for everyone"
echo "✅ Complete analysis functionality"
echo "✅ Free hosting on Streamlit Cloud"
