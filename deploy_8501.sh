#!/bin/bash

# BuzzScope 8501端口部署脚本
echo "🚀 Preparing BuzzScope Historical Analysis (Port 8501) for deployment..."

# 检查必要文件
if [ ! -f "app_simple_historical.py" ]; then
    echo "❌ app_simple_historical.py not found"
    exit 1
fi

if [ ! -d "data/cache" ]; then
    echo "❌ data/cache directory not found"
    exit 1
fi

# 创建部署目录
echo "📁 Creating deployment directory..."
mkdir -p buzzscope-8501-deploy
cd buzzscope-8501-deploy

# 复制必要文件
echo "📋 Copying files..."
cp ../app_simple_historical.py .
cp ../requirements.txt .
cp -r ../data/cache .
cp -r ../src .

# 创建README
cat > README.md << 'EOF'
# BuzzScope Historical Analysis

## 🎯 功能
- 历史数据分析 (Hacker News, Reddit, YouTube, Discord)
- 关键词趋势分析
- 跨平台对比
- 预缓存数据，快速加载

## 🚀 部署到Streamlit Cloud

1. 将代码推送到GitHub
2. 访问 [share.streamlit.io](https://share.streamlit.io)
3. 选择 `app_simple_historical.py` 作为主文件
4. 部署！

## 📊 数据说明
- 包含预处理的缓存数据
- 支持关键词: ai, iot, mqtt, unified_namespace
- 数据来源: Hacker News (2年), Reddit, YouTube, Discord

## 🔧 本地运行
```bash
streamlit run app_simple_historical.py --server.port 8501
```
EOF

# 创建.gitignore
cat > .gitignore << 'EOF'
# 环境变量
.env
.env.backup

# Python缓存
__pycache__/
*.pyc
*.pyo
*.pyd

# 系统文件
.DS_Store
Thumbs.db

# 日志文件
*.log
EOF

echo "✅ Deployment package created in buzzscope-8501-deploy/"
echo ""
echo "📋 Next steps:"
echo "1. cd buzzscope-8501-deploy"
echo "2. git init"
echo "3. git add ."
echo "4. git commit -m 'BuzzScope Historical Analysis'"
echo "5. Create GitHub repository and push"
echo "6. Deploy on Streamlit Cloud"
echo ""
echo "🌐 The app will be accessible at: https://your-app-name.streamlit.app"


