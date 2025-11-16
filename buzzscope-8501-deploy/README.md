# BuzzScope: Where technology speaks, and you feel the echo

## 🔍 Historical Analysis Dashboard

A comprehensive technology trend analysis platform that analyzes keyword mentions across multiple platforms using pre-cached historical data.

### 🎯 Features

- **Multi-Platform Analysis**: Hacker News, Reddit, YouTube, Discord
- **Pre-cached Data**: Fast loading with 2+ years of historical data
- **Trend Visualization**: Monthly trend charts and statistics
- **Cross-Platform Comparison**: Compare keyword performance across platforms
- **Top Contributors**: Identify key influencers and contributors
- **Interactive Charts**: Plotly-powered visualizations

### 📊 Supported Keywords

- **ai** - Artificial Intelligence
- **iot** - Internet of Things  
- **mqtt** - MQTT Protocol
- **unified_namespace** - Unified Namespace

### 🚀 Live Demo

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app)

### 📈 Data Sources

- **Hacker News**: 2 years of historical data (stories, comments, Show HN, Ask HN)
- **Reddit**: Keyword-related posts and discussions
- **YouTube**: Video content and engagement metrics
- **Discord**: Community discussions (Industry 4.0, supOS, SOLISCADA)

### 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas, Plotly
- **Data Sources**: Hacker News API, Reddit JSON API, YouTube Data API v3
- **Visualization**: Plotly charts, interactive dashboards

### 📋 Usage

1. **Select Keywords**: Choose from predefined keywords or enter custom ones
2. **Choose Platforms**: Select which platforms to analyze
3. **View Analysis**: Explore trends, top posts, and contributor insights
4. **Compare Platforms**: Use multi-platform comparison features

### 🔧 Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/buzzscope-historical.git
cd buzzscope-historical

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app_simple_historical.py --server.port 8501
```

### 📊 Data Structure

```
cache/
├── hackernews/          # Hacker News data
├── reddit/             # Reddit posts
├── youtube/            # YouTube videos
├── discord/            # Discord messages
└── charts/             # Pre-generated trend charts
```

### 🎨 Key Metrics

- **Total Posts**: Number of posts mentioning the keyword
- **Unique Authors**: Number of unique contributors
- **Total Interactions**: Sum of scores, comments, and engagement
- **Monthly Trends**: Time-series analysis of keyword mentions
- **Top Contributors**: Most active users across platforms

### 🔍 Analysis Features

- **Trend Analysis**: Monthly mention patterns
- **Platform Comparison**: Cross-platform performance metrics
- **Top Posts**: Most engaging content
- **Contributor Analysis**: Key influencers and their impact
- **Engagement Metrics**: Comments, scores, and interaction data

### 📱 Responsive Design

- Optimized for desktop and mobile viewing
- Interactive charts and tables
- Clean, modern interface
- Fast loading with pre-cached data

### 🚀 Deployment

This application is deployed on Streamlit Cloud and uses pre-cached historical data for fast performance. No API keys or real-time data collection is required.

### 📄 License

This project is open source and available under the MIT License.

### 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### 📞 Contact

For questions or suggestions, please open an issue on GitHub.

---

**Note**: This is a historical analysis tool using pre-cached data. For real-time monitoring, please refer to the main BuzzScope repository.